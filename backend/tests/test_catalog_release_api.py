"""目录发布治理接口的端到端测试：走完整 REST 流程。"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
CAT = "CAT-API"


def _build_catalog() -> None:
    for feature in ["A", "B", "C", "D", "F"]:
        resp = client.post(f"/api/catalog-release/catalogs/{CAT}/members",
                           json={"feature": feature})
        assert resp.status_code == 200, resp.text
    for upstream, downstream in [
        ("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("E", "A"),
    ]:
        resp = client.post(f"/api/catalog-release/catalogs/{CAT}/edges",
                           json={"upstream": upstream, "downstream": downstream})
        assert resp.status_code == 200, resp.text


def test_catalog_release_flow_over_http():
    _build_catalog()

    # 新增目录预览：影响明细分三档呈现
    preview = client.post(f"/api/catalog-release/catalogs/{CAT}/previews").json()
    assert preview["direct_changes"] == ["A", "F"]
    assert [n["feature"] for n in preview["downstream_review"]] == ["B", "C", "D"]
    assert [n["feature"] for n in preview["upstream_evidence"]] == ["E"]
    d_node = next(n for n in preview["downstream_review"] if n["feature"] == "D")
    assert [[e["label"] for e in path] for path in d_node["paths"]] == [
        ["A->B", "B->D"], ["A->C", "C->D"],
    ]

    # 治理审计：待审清单中 D 一个身份两条路径，E 无待审项
    batch = client.post(
        f"/api/catalog-release/previews/{preview['preview_id']}/audit-batches").json()
    assert [item["feature"] for item in batch["items"]] == ["B", "C", "D"]
    assert all(item["feature"] != "E" for item in batch["items"])
    assert batch["snapshot"]["members"] == ["A", "B", "C", "D", "F"]

    # F 签完、D 尚未签字时签发
    for feature in ["A", "B", "C", "F"]:
        client.post("/api/catalog-release/signoffs",
                    json={"feature": feature, "signer": "治理组-甲"})
    receipt = client.post(
        f"/api/catalog-release/previews/{preview['preview_id']}/publish",
        json={"action_key": "PUB-API-1", "signer": "签发人-乙"}).json()
    assert receipt["released"] == ["A", "B", "C", "F"]
    assert receipt["held"] == [{"feature": "D", "reason": "签字核查未完成"}]

    # 立即从消费端请求 F：拿到可用成员；D 是带明确原因的待交付状态
    got_f = client.get("/api/catalog-release/consumer/features/F").json()
    assert got_f["status"] == "可用"
    got_d = client.get("/api/catalog-release/consumer/features/D").json()
    assert got_d["status"] == "待交付"
    assert got_d["reason"] == "签字核查未完成"

    # 同一发布动作重复提交不产生重复交付
    again = client.post(
        f"/api/catalog-release/previews/{preview['preview_id']}/publish",
        json={"action_key": "PUB-API-1", "signer": "签发人-乙"}).json()
    assert again["released"] == ["A", "B", "C", "F"]

    # D 补签后重新签发：实际新增范围只有 D
    client.post("/api/catalog-release/signoffs",
                json={"feature": "D", "signer": "治理组-丙"})
    republish = client.post(
        f"/api/catalog-release/previews/{preview['preview_id']}/publish",
        json={"action_key": "PUB-API-2", "signer": "签发人-乙"}).json()
    assert republish["released"] == ["D"]
    assert republish["already_released"] == ["A", "B", "C", "F"]
    assert client.get(
        "/api/catalog-release/consumer/features/D").json()["status"] == "可用"
