"""目录发布治理的场景测试：目录预览 → 待审清单 → 整笔签发 → 消费端可见性。

场景：目录成员 A、B、C、D、F；血缘边 A→B、A→C、B→D、C→D；
E 在目录外（E→A），是未签字的来源依赖；F 是不共享该依赖的独立成员。
"""
from __future__ import annotations

import pytest

from app.services.catalog_release import (
    Availability,
    CatalogReleaseHub,
    LineageEdge,
    PublishPolicy,
)

CAT = "CAT-001"


@pytest.fixture()
def hub() -> CatalogReleaseHub:
    hub = CatalogReleaseHub()
    for feature in ["A", "B", "C", "D", "F"]:
        hub.graph.add_member(CAT, feature)
    for upstream, downstream in [
        ("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("E", "A"),
    ]:
        hub.graph.add_edge(CAT, upstream, downstream)
    return hub


def labels(paths) -> list[tuple[str, ...]]:
    return [tuple(str(edge) for edge in path) for path in paths]


# ---------------------------------------------------------------------------
# 目录预览与目录影响明细
# ---------------------------------------------------------------------------


def test_preview_splits_impact_into_three_buckets(hub):
    preview = hub.previews.create_preview(CAT)

    # 直接变更：目录内没有上游成员的 A 与独立成员 F
    assert preview.direct_changes == ("A", "F")
    # 待核查的下游：B、C、D
    assert [node.feature for node in preview.downstream_review] == ["B", "C", "D"]
    # 仅作来源证据的上游：目录外的 E
    assert [node.feature for node in preview.upstream_evidence] == ["E"]
    assert preview.cycles == ()


def test_diamond_node_counted_once_with_two_traceable_paths(hub):
    preview = hub.previews.create_preview(CAT)

    downstream = {node.feature: node for node in preview.downstream_review}
    # 同一个衍生特征 D 由两条目录路径抵达，只计一次
    assert list(downstream).count("D") == 1
    # 但两条路径都可回查：A→B→D 与 A→C→D
    assert sorted(labels(downstream["D"].paths)) == [
        ("A->B", "B->D"),
        ("A->C", "C->D"),
    ]
    assert labels(downstream["B"].paths) == [("A->B",)]
    assert labels(downstream["C"].paths) == [("A->C",)]


def test_cycle_lists_traversed_edges_and_stops(hub):
    for feature in ["W", "X", "Y", "Z"]:
        hub.graph.add_member("CAT-CYCLE", feature)
    for upstream, downstream in [
        ("W", "X"), ("X", "Y"), ("Y", "Z"), ("Z", "X"),
    ]:
        hub.graph.add_edge("CAT-CYCLE", upstream, downstream)

    preview = hub.previews.create_preview("CAT-CYCLE")

    # 遇到环：列出环段上经过的边并停止沿环扩展；同一个环只列一次
    assert len(preview.cycles) == 1
    assert [str(edge) for edge in preview.cycles[0].edges] == [
        "X->Y", "Y->Z", "Z->X",
    ]
    # 环上的节点仍只计一次，且遍历正常终止
    assert [node.feature for node in preview.downstream_review] == ["X", "Y", "Z"]


# ---------------------------------------------------------------------------
# 治理审计：待审清单与快照引用
# ---------------------------------------------------------------------------


def test_audit_batch_one_identity_per_node_and_none_for_upstream(hub):
    preview = hub.previews.create_preview(CAT)
    batch = hub.audits.open_batch(preview.preview_id)

    # 待审清单只覆盖待核查的下游
    assert [item.feature for item in batch.items] == ["B", "C", "D"]
    # D 只建立一个待审身份，并能回查两条路径
    d_items = [item for item in batch.items if item.feature == "D"]
    assert len(d_items) == 1
    assert sorted(labels(d_items[0].paths)) == [
        ("A->B", "B->D"),
        ("A->C", "C->D"),
    ]
    # E 仅作来源证据，保持无待审项
    assert batch.item_for("E") is None


def test_audit_batch_pins_the_snapshot_of_one_preview(hub):
    preview = hub.previews.create_preview(CAT)

    # 预览之后并发发生目录成员变更与确认
    hub.graph.add_member(CAT, "G")
    hub.graph.add_edge(CAT, "F", "G")
    hub.signoffs.sign("A", "治理组-甲")

    # 审计批只能引用该次预览所使用的完整成员与边集合
    batch = hub.audits.open_batch(preview.preview_id)
    assert batch.snapshot == preview.snapshot
    assert batch.snapshot.members == frozenset({"A", "B", "C", "D", "F"})
    assert batch.snapshot.edges == frozenset({
        LineageEdge("A", "B"), LineageEdge("A", "C"),
        LineageEdge("B", "D"), LineageEdge("C", "D"), LineageEdge("E", "A"),
    })
    assert batch.item_for("G") is None

    # 新预览才能看到变更后的成员与边
    newer = hub.previews.create_preview(CAT)
    assert newer.snapshot.version > preview.snapshot.version
    assert "G" in newer.snapshot.members
    assert LineageEdge("F", "G") in newer.snapshot.edges


# ---------------------------------------------------------------------------
# 签发与消费端可见性
# ---------------------------------------------------------------------------


def _sign_reviewed_members(hub: CatalogReleaseHub) -> None:
    # 同批成员中 A、B、C 与独立成员 F 已核完；D 尚未签字；E 在目录外不签
    for feature in ["A", "B", "C", "F"]:
        hub.signoffs.sign(feature, "治理组-甲")


def test_first_publish_releases_signed_independent_member(hub):
    _sign_reviewed_members(hub)
    preview = hub.previews.create_preview(CAT)
    hub.audits.open_batch(preview.preview_id)

    receipt = hub.desk.submit(preview.preview_id, action_key="PUB-1", signer="签发人-乙")

    # 发布策略按成员独立放行：已签字的成员（含独立成员 F）立即交付，
    # 不为尚未签字的 D 设置全局屏障
    assert receipt.released == ("A", "B", "C", "F")
    assert [(hold.feature, hold.reason) for hold in receipt.held] == [
        ("D", PublishPolicy.REASON_UNSIGNED),
    ]
    assert receipt.already_released == ()

    # 消费端随即按实际签发结果选择：F 可用
    got_f = hub.consumer.fetch("F")
    assert got_f.status == Availability.AVAILABLE
    assert got_f.release is not None and got_f.release.action_key == "PUB-1"

    # D 是有明确原因的待交付状态
    got_d = hub.consumer.fetch("D")
    assert got_d.status == Availability.PENDING
    assert got_d.reason == PublishPolicy.REASON_UNSIGNED


def test_publish_action_is_submitted_only_once(hub):
    _sign_reviewed_members(hub)
    preview = hub.previews.create_preview(CAT)

    first = hub.desk.submit(preview.preview_id, action_key="PUB-1", signer="签发人-乙")
    again = hub.desk.submit(preview.preview_id, action_key="PUB-1", signer="签发人-乙")

    assert again is first
    assert again.released == ("A", "B", "C", "F")


def test_republish_after_supplementary_signoff_delivers_only_new_scope(hub):
    _sign_reviewed_members(hub)
    preview = hub.previews.create_preview(CAT)
    hub.desk.submit(preview.preview_id, action_key="PUB-1", signer="签发人-乙")

    # D 补签后重新签发
    hub.signoffs.sign("D", "治理组-丙")
    receipt = hub.desk.submit(preview.preview_id, action_key="PUB-2", signer="签发人-乙")

    # 实际新增范围只有 D，已交付成员不重复交付
    assert receipt.released == ("D",)
    assert receipt.already_released == ("A", "B", "C", "F")
    assert receipt.held == ()

    assert hub.consumer.fetch("D").status == Availability.AVAILABLE
    release_f = hub.consumer.fetch("F").release
    assert release_f is not None and release_f.action_key == "PUB-1"


def test_upstream_evidence_out_of_delivery_scope(hub):
    _sign_reviewed_members(hub)
    preview = hub.previews.create_preview(CAT)
    receipt = hub.desk.submit(preview.preview_id, action_key="PUB-1", signer="签发人-乙")

    # 目录外的 E 未签字，但不属于交付范围：不在交付或暂缓之列，也不阻塞 A
    assert "E" not in preview.scope
    assert "E" not in receipt.released
    assert all(hold.feature != "E" for hold in receipt.held)
    assert "A" in receipt.released
    assert hub.consumer.fetch("E").status == Availability.UNPUBLISHED


def test_consumer_reports_unpublished_for_unknown_feature(hub):
    assert hub.consumer.fetch("不存在").status == Availability.UNPUBLISHED
