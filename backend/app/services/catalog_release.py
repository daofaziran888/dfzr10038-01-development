"""目录发布治理：目录预览 → 目录影响明细 → 待审清单 → 整笔签发 → 消费端可见性。

发布特征目录前，先由目录预览冻结一份完整的成员与血缘边快照，
据快照生成目录影响明细，并分三档呈现：

- 直接变更：目录内没有上游成员的目录成员（本批变更的源头）；
- 待核查的下游：从直接变更沿血缘边可达的节点，需治理核查后才能交付；
- 仅作来源证据的上游：目录外的上游节点，只作证据，不产生待审项、
  也不属于交付范围。

语义约定：

- 同一衍生特征被多条目录路径抵达时只计一次，但保留全部路径供回查；
- 遍历遇到环时列出经过的边，并停止沿环扩展；
- 目录成员变更与确认并发时，审计批只引用一次预览所使用的完整成员与
  边集合（快照不可变，之后的目录变更需要新的预览）；
- 发布策略按成员独立放行：成员自身签字齐全即交付，不为同批无关的
  待签成员设置全局屏障；补签后重新签发只交付实际新增范围，不重复交付；
- 签发人员提交的整笔发布动作凭幂等键只生效一次。
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from enum import Enum


# ---------------------------------------------------------------------------
# 血缘图与版本化快照
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LineageEdge:
    """一条血缘边：上游特征 → 下游特征。"""

    upstream: str
    downstream: str

    def __str__(self) -> str:
        return f"{self.upstream}->{self.downstream}"


@dataclass(frozen=True)
class CatalogSnapshot:
    """某次预览冻结的完整成员与边集合（审计批只能引用这一份）。"""

    catalog_id: str
    version: int
    members: frozenset[str]
    edges: frozenset[LineageEdge]


class CatalogGraph:
    """目录图存储：目录成员与关联血缘边，按版本演进。

    成员变更与签字确认可以并发进行；每次预览通过 snapshot() 冻结一份
    完整成员与边集合，之后的变更不影响已生成的预览与审计批。
    """

    def __init__(self) -> None:
        self._members: dict[str, set[str]] = {}
        self._edges: dict[str, set[LineageEdge]] = {}
        self._versions: dict[str, int] = {}

    def _touch(self, catalog_id: str) -> None:
        self._members.setdefault(catalog_id, set())
        self._edges.setdefault(catalog_id, set())
        self._versions.setdefault(catalog_id, 0)

    def add_member(self, catalog_id: str, feature: str) -> int:
        self._touch(catalog_id)
        self._members[catalog_id].add(feature)
        self._versions[catalog_id] += 1
        return self._versions[catalog_id]

    def add_edge(self, catalog_id: str, upstream: str, downstream: str) -> int:
        self._touch(catalog_id)
        self._edges[catalog_id].add(LineageEdge(upstream, downstream))
        self._versions[catalog_id] += 1
        return self._versions[catalog_id]

    def snapshot(self, catalog_id: str) -> CatalogSnapshot:
        self._touch(catalog_id)
        return CatalogSnapshot(
            catalog_id=catalog_id,
            version=self._versions[catalog_id],
            members=frozenset(self._members[catalog_id]),
            edges=frozenset(self._edges[catalog_id]),
        )


# ---------------------------------------------------------------------------
# 血缘遍历：全部简单路径 + 环检测
# ---------------------------------------------------------------------------


def _walk_paths(
    roots: tuple[str, ...],
    steps: dict[str, tuple[tuple[LineageEdge, str], ...]],
) -> tuple[dict[str, list[tuple[LineageEdge, ...]]], list[tuple[LineageEdge, ...]]]:
    """从 roots 出发枚举全部简单路径。

    返回 (paths, cycles)：
    - paths：节点 -> 抵达该节点的全部简单路径（每条路径是一串血缘边）；
    - cycles：遇到的环，只保留环段上经过的边（从首次进入环的节点起），
      扩展在闭合边处停止，不再沿环继续。
    """
    paths: dict[str, list[tuple[LineageEdge, ...]]] = {}
    cycles: list[tuple[LineageEdge, ...]] = []
    stack = [(root, (root,), ()) for root in roots]
    while stack:
        node, seen, edges = stack.pop()
        for edge, nxt in steps.get(node, ()):
            if nxt in seen:
                cycles.append(edges[seen.index(nxt):] + (edge,))
                continue
            path = edges + (edge,)
            paths.setdefault(nxt, []).append(path)
            stack.append((nxt, seen + (nxt,), path))
    return paths, cycles


def _downstream_steps(edges: frozenset[LineageEdge]) -> dict[str, tuple[tuple[LineageEdge, str], ...]]:
    steps: dict[str, list[tuple[LineageEdge, str]]] = {}
    for edge in edges:
        steps.setdefault(edge.upstream, []).append((edge, edge.downstream))
    return {node: tuple(sorted(items, key=lambda item: str(item[0]))) for node, items in steps.items()}


def _upstream_steps(edges: frozenset[LineageEdge]) -> dict[str, tuple[tuple[LineageEdge, str], ...]]:
    steps: dict[str, list[tuple[LineageEdge, str]]] = {}
    for edge in edges:
        steps.setdefault(edge.downstream, []).append((edge, edge.upstream))
    return {node: tuple(sorted(items, key=lambda item: str(item[0]))) for node, items in steps.items()}


def _sort_paths(paths: list[tuple[LineageEdge, ...]]) -> tuple[tuple[LineageEdge, ...], ...]:
    return tuple(sorted(paths, key=lambda path: tuple(str(edge) for edge in path)))


def _dedup_cycles(
    down_cycles: list[tuple[LineageEdge, ...]],
    up_cycles: list[tuple[LineageEdge, ...]],
) -> list[tuple[LineageEdge, ...]]:
    """按环的边集合去重：下游（影响方向）的呈现优先，上游环反转为自然方向。"""
    seen: set[frozenset[LineageEdge]] = set()
    unique: list[tuple[LineageEdge, ...]] = []
    for edges in list(down_cycles) + [tuple(reversed(path)) for path in up_cycles]:
        key = frozenset(edges)
        if key not in seen:
            seen.add(key)
            unique.append(edges)
    return sorted(unique, key=lambda path: tuple(str(edge) for edge in path))


# ---------------------------------------------------------------------------
# 目录预览与目录影响明细
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ImpactNode:
    """影响明细中的一个节点：只计一次，保留全部抵达路径供回查。"""

    feature: str
    paths: tuple[tuple[LineageEdge, ...], ...]


@dataclass(frozen=True)
class CycleHit:
    """遍历遇到的环：列出经过的边，扩展在末条边处停止。"""

    edges: tuple[LineageEdge, ...]


@dataclass(frozen=True)
class CatalogPreview:
    """目录预览：一份快照，以及由它生成的目录影响明细。"""

    preview_id: str
    snapshot: CatalogSnapshot
    direct_changes: tuple[str, ...]
    downstream_review: tuple[ImpactNode, ...]
    upstream_evidence: tuple[ImpactNode, ...]
    cycles: tuple[CycleHit, ...]

    @property
    def scope(self) -> tuple[str, ...]:
        """交付范围 = 直接变更 + 待核查的下游（上游证据不在交付范围内）。"""
        return self.direct_changes + tuple(node.feature for node in self.downstream_review)


class PreviewEngine:
    """目录预览：冻结快照，生成直接变更 / 待核查下游 / 来源证据上游三档明细。"""

    def __init__(self, graph: CatalogGraph) -> None:
        self._graph = graph
        self._previews: dict[str, CatalogPreview] = {}
        self._seq = itertools.count(1)

    def create_preview(self, catalog_id: str) -> CatalogPreview:
        snap = self._graph.snapshot(catalog_id)
        direct = tuple(sorted(
            member for member in snap.members
            if not any(
                edge.downstream == member and edge.upstream in snap.members
                for edge in snap.edges
            )
        ))
        down_paths, down_cycles = _walk_paths(direct, _downstream_steps(snap.edges))
        up_paths, up_cycles = _walk_paths(tuple(sorted(snap.members)), _upstream_steps(snap.edges))

        downstream_review = tuple(
            ImpactNode(feature, _sort_paths(down_paths[feature]))
            for feature in sorted(down_paths)
            if feature not in direct
        )
        upstream_evidence = tuple(
            ImpactNode(
                feature,
                # 上游路径按「来源 → 成员」的自然方向呈现，便于证据回查
                _sort_paths([tuple(reversed(path)) for path in up_paths[feature]]),
            )
            for feature in sorted(up_paths)
            if feature not in snap.members
        )
        # 同一个环可能被两个方向、多个起点的遍历重复遇到：按环的边集合去重，
        # 只列一次；上游方向遇到的环按「来源 → 成员」的自然方向呈现。
        cycles = tuple(
            CycleHit(edges)
            for edges in _dedup_cycles(down_cycles, up_cycles)
        )
        preview = CatalogPreview(
            preview_id=f"PRE-{next(self._seq):04d}",
            snapshot=snap,
            direct_changes=direct,
            downstream_review=downstream_review,
            upstream_evidence=upstream_evidence,
            cycles=cycles,
        )
        self._previews[preview.preview_id] = preview
        return preview

    def get(self, preview_id: str) -> CatalogPreview:
        if preview_id not in self._previews:
            raise KeyError(f"目录预览 {preview_id} 不存在")
        return self._previews[preview_id]


# ---------------------------------------------------------------------------
# 治理审计：待审清单
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReviewItem:
    """待审清单中的一项：一个待核查身份 + 需要核查的血缘路径。"""

    feature: str
    paths: tuple[tuple[LineageEdge, ...], ...]


@dataclass(frozen=True)
class AuditBatch:
    """审计批：只引用一次预览所使用的完整成员与边集合。"""

    batch_id: str
    preview_id: str
    snapshot: CatalogSnapshot
    items: tuple[ReviewItem, ...]

    def item_for(self, feature: str) -> ReviewItem | None:
        for item in self.items:
            if item.feature == feature:
                return item
        return None


class AuditOffice:
    """治理审计：根据目录影响明细生成带血缘路径的待审清单。"""

    def __init__(self, previews: PreviewEngine) -> None:
        self._previews = previews
        self._batches: dict[str, AuditBatch] = {}
        self._seq = itertools.count(1)

    def open_batch(self, preview_id: str) -> AuditBatch:
        preview = self._previews.get(preview_id)
        # 待审项只来自「待核查的下游」；仅作来源证据的上游不产生待审项。
        # 同一节点无论被几条路径抵达，都只建立一个待审身份。
        items = tuple(
            ReviewItem(node.feature, node.paths) for node in preview.downstream_review
        )
        batch = AuditBatch(
            batch_id=f"AUD-{next(self._seq):04d}",
            preview_id=preview.preview_id,
            snapshot=preview.snapshot,
            items=items,
        )
        self._batches[batch.batch_id] = batch
        return batch

    def get(self, batch_id: str) -> AuditBatch:
        if batch_id not in self._batches:
            raise KeyError(f"审计批 {batch_id} 不存在")
        return self._batches[batch_id]


# ---------------------------------------------------------------------------
# 签字台账
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Signoff:
    feature: str
    signer: str
    note: str = ""


class SignoffBook:
    """签字台账：特征粒度的核准确认，支持补签。"""

    def __init__(self) -> None:
        self._records: dict[str, Signoff] = {}

    def sign(self, feature: str, signer: str, note: str = "") -> Signoff:
        record = Signoff(feature=feature, signer=signer, note=note)
        self._records[feature] = record
        return record

    def is_signed(self, feature: str) -> bool:
        return feature in self._records

    def get(self, feature: str) -> Signoff | None:
        return self._records.get(feature)


# ---------------------------------------------------------------------------
# 签发台与发布策略
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HeldBack:
    """因发布策略暂缓交付的成员，附带明确原因。"""

    feature: str
    reason: str


@dataclass(frozen=True)
class Release:
    """一次实际交付记录。"""

    feature: str
    action_key: str
    preview_id: str
    version: int


@dataclass(frozen=True)
class PublishReceipt:
    """整笔发布动作的结果。"""

    action_key: str
    preview_id: str
    version: int
    submitted_by: str
    released: tuple[str, ...]          # 本次实际新增交付
    held: tuple[HeldBack, ...]         # 本次暂缓及原因
    already_released: tuple[str, ...]  # 此前已交付，本次不重复交付


class PublishPolicy:
    """发布策略：明确何时给同批的独立成员放行。

    - 按成员独立评估：成员自身签字齐全即放行，不因同批其他成员
      （例如共享目录外未签字依赖的下游）尚未核查而设置全局屏障；
    - 已交付成员永久有效：补签后重新签发只交付实际新增范围，不重复交付；
    - 目录外的上游证据不属于交付范围，其签字状态不影响任何成员放行。
    """

    REASON_UNSIGNED = "签字核查未完成"

    def hold_reason(self, feature: str, signoffs: SignoffBook) -> str | None:
        """返回 None 表示放行，否则返回暂缓的明确原因。"""
        if not signoffs.is_signed(feature):
            return self.REASON_UNSIGNED
        return None


class PublishDesk:
    """签发台：签发人员提交整笔发布动作；同一动作凭幂等键只提交一次。"""

    def __init__(
        self,
        previews: PreviewEngine,
        signoffs: SignoffBook,
        policy: PublishPolicy | None = None,
    ) -> None:
        self._previews = previews
        self._signoffs = signoffs
        self._policy = policy or PublishPolicy()
        self._releases: dict[str, Release] = {}
        self._held: dict[str, HeldBack] = {}
        self._actions: dict[str, PublishReceipt] = {}

    def submit(self, preview_id: str, action_key: str, signer: str) -> PublishReceipt:
        if action_key in self._actions:
            return self._actions[action_key]
        preview = self._previews.get(preview_id)
        released: list[str] = []
        held: list[HeldBack] = []
        already: list[str] = []
        for feature in preview.scope:
            if feature in self._releases:
                already.append(feature)
                continue
            reason = self._policy.hold_reason(feature, self._signoffs)
            if reason is None:
                self._releases[feature] = Release(
                    feature=feature,
                    action_key=action_key,
                    preview_id=preview.preview_id,
                    version=preview.snapshot.version,
                )
                self._held.pop(feature, None)
                released.append(feature)
            else:
                hold = HeldBack(feature=feature, reason=reason)
                self._held[feature] = hold
                held.append(hold)
        receipt = PublishReceipt(
            action_key=action_key,
            preview_id=preview.preview_id,
            version=preview.snapshot.version,
            submitted_by=signer,
            released=tuple(sorted(released)),
            held=tuple(sorted(held, key=lambda hold: hold.feature)),
            already_released=tuple(sorted(already)),
        )
        self._actions[action_key] = receipt
        return receipt

    def release_for(self, feature: str) -> Release | None:
        return self._releases.get(feature)

    def held_for(self, feature: str) -> HeldBack | None:
        return self._held.get(feature)


# ---------------------------------------------------------------------------
# 消费端视图
# ---------------------------------------------------------------------------


class Availability(str, Enum):
    AVAILABLE = "可用"
    PENDING = "待交付"
    UNPUBLISHED = "未发布"


@dataclass(frozen=True)
class ConsumerResult:
    feature: str
    status: Availability
    reason: str | None = None
    release: Release | None = None


class ConsumerView:
    """目录使用者视图：按实际签发结果选择可用特征。"""

    def __init__(self, desk: PublishDesk) -> None:
        self._desk = desk

    def fetch(self, feature: str) -> ConsumerResult:
        release = self._desk.release_for(feature)
        if release is not None:
            return ConsumerResult(feature=feature, status=Availability.AVAILABLE, release=release)
        held = self._desk.held_for(feature)
        if held is not None:
            return ConsumerResult(feature=feature, status=Availability.PENDING, reason=held.reason)
        return ConsumerResult(feature=feature, status=Availability.UNPUBLISHED)


# ---------------------------------------------------------------------------
# 组合门面与演示数据
# ---------------------------------------------------------------------------


class CatalogReleaseHub:
    """组合目录图、预览、审计、签字、签发与消费视图的门面。"""

    def __init__(self) -> None:
        self.graph = CatalogGraph()
        self.previews = PreviewEngine(self.graph)
        self.audits = AuditOffice(self.previews)
        self.signoffs = SignoffBook()
        self.desk = PublishDesk(self.previews, self.signoffs)
        self.consumer = ConsumerView(self.desk)


def seed_demo(hub: CatalogReleaseHub, catalog_id: str = "CAT-DEMO") -> None:
    """演示目录：A→B、A→C、B→D、C→D，独立成员 F，目录外的上游 E。"""
    for feature in ["A", "B", "C", "D", "F"]:
        hub.graph.add_member(catalog_id, feature)
    for upstream, downstream in [
        ("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("E", "A"),
    ]:
        hub.graph.add_edge(catalog_id, upstream, downstream)


hub = CatalogReleaseHub()
seed_demo(hub)
