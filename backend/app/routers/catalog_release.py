"""目录发布治理接口：目录预览、目录影响明细、待审清单、整笔签发与消费端查询。

状态流转只允许发生在 app/services；这里只做参数校验、序列化和错误映射。
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.catalog_release import (
    AuditBatch,
    CatalogPreview,
    CatalogSnapshot,
    ConsumerResult,
    LineageEdge,
    PublishReceipt,
    hub,
)

router = APIRouter(prefix="/api/catalog-release", tags=["目录发布治理"])


class MemberPayload(BaseModel):
    feature: str


class EdgePayload(BaseModel):
    upstream: str
    downstream: str


class SignoffPayload(BaseModel):
    feature: str
    signer: str
    note: str = ""


class PublishPayload(BaseModel):
    action_key: str = Field(description="幂等键：同一发布动作只提交一次")
    signer: str


def _edge(edge: LineageEdge) -> dict[str, Any]:
    return {"upstream": edge.upstream, "downstream": edge.downstream, "label": str(edge)}


def _snapshot(snapshot: CatalogSnapshot) -> dict[str, Any]:
    return {
        "catalog_id": snapshot.catalog_id,
        "version": snapshot.version,
        "members": sorted(snapshot.members),
        "edges": [_edge(edge) for edge in sorted(snapshot.edges, key=str)],
    }


def _impact_node(node) -> dict[str, Any]:
    return {
        "feature": node.feature,
        "paths": [[_edge(edge) for edge in path] for path in node.paths],
    }


def _preview(preview: CatalogPreview) -> dict[str, Any]:
    return {
        "preview_id": preview.preview_id,
        "snapshot": _snapshot(preview.snapshot),
        "direct_changes": list(preview.direct_changes),
        "downstream_review": [_impact_node(node) for node in preview.downstream_review],
        "upstream_evidence": [_impact_node(node) for node in preview.upstream_evidence],
        "cycles": [{"edges": [_edge(edge) for edge in hit.edges]} for hit in preview.cycles],
        "scope": list(preview.scope),
    }


def _batch(batch: AuditBatch) -> dict[str, Any]:
    return {
        "batch_id": batch.batch_id,
        "preview_id": batch.preview_id,
        "snapshot": _snapshot(batch.snapshot),
        "items": [
            {
                "feature": item.feature,
                "paths": [[_edge(edge) for edge in path] for path in item.paths],
            }
            for item in batch.items
        ],
    }


def _receipt(receipt: PublishReceipt) -> dict[str, Any]:
    return {
        "action_key": receipt.action_key,
        "preview_id": receipt.preview_id,
        "version": receipt.version,
        "submitted_by": receipt.submitted_by,
        "released": list(receipt.released),
        "held": [{"feature": hold.feature, "reason": hold.reason} for hold in receipt.held],
        "already_released": list(receipt.already_released),
    }


def _consumer(result: ConsumerResult) -> dict[str, Any]:
    return {
        "feature": result.feature,
        "status": result.status.value,
        "reason": result.reason,
        "release": (
            {
                "action_key": result.release.action_key,
                "preview_id": result.release.preview_id,
                "version": result.release.version,
            }
            if result.release
            else None
        ),
    }


@router.get("/catalogs/{catalog_id}")
def get_catalog(catalog_id: str) -> dict[str, Any]:
    """查看目录当前的完整成员与边集合（最新版本）。"""
    return _snapshot(hub.graph.snapshot(catalog_id))


@router.post("/catalogs/{catalog_id}/members")
def add_member(catalog_id: str, payload: MemberPayload) -> dict[str, Any]:
    version = hub.graph.add_member(catalog_id, payload.feature.strip())
    return {"ok": True, "version": version}


@router.post("/catalogs/{catalog_id}/edges")
def add_edge(catalog_id: str, payload: EdgePayload) -> dict[str, Any]:
    version = hub.graph.add_edge(catalog_id, payload.upstream.strip(), payload.downstream.strip())
    return {"ok": True, "version": version}


@router.post("/catalogs/{catalog_id}/previews")
def create_preview(catalog_id: str) -> dict[str, Any]:
    """新增目录预览：冻结快照并生成目录影响明细。"""
    return _preview(hub.previews.create_preview(catalog_id))


@router.get("/previews/{preview_id}")
def get_preview(preview_id: str) -> dict[str, Any]:
    try:
        return _preview(hub.previews.get(preview_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/previews/{preview_id}/audit-batches")
def open_audit_batch(preview_id: str) -> dict[str, Any]:
    """治理审计：根据目录影响明细生成带血缘路径的待审清单。"""
    try:
        return _batch(hub.audits.open_batch(preview_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/audit-batches/{batch_id}")
def get_audit_batch(batch_id: str) -> dict[str, Any]:
    try:
        return _batch(hub.audits.get(batch_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/signoffs")
def sign(payload: SignoffPayload) -> dict[str, Any]:
    """签字确认（含补签）。"""
    record = hub.signoffs.sign(payload.feature.strip(), payload.signer.strip(), payload.note)
    return {"ok": True, "feature": record.feature, "signer": record.signer}


@router.post("/previews/{preview_id}/publish")
def publish(preview_id: str, payload: PublishPayload) -> dict[str, Any]:
    """签发人员提交整笔发布动作；同一 action_key 只生效一次。"""
    try:
        receipt = hub.desk.submit(preview_id, payload.action_key.strip(), payload.signer.strip())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _receipt(receipt)


@router.get("/consumer/features/{feature}")
def consumer_fetch(feature: str) -> dict[str, Any]:
    """目录使用者按实际签发结果查询特征：可用 / 待交付（带原因）/ 未发布。"""
    return _consumer(hub.consumer.fetch(feature))
