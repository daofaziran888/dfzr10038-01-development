"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class FeatureLineService(BaseModuleService):
    MODULE = "feature_line"
    ENTITY = "血缘链路"
    OPERATION_TERM = "转换"
    LIST_FIELDS = ["链路编号", "上游特征", "下游特征", "转换函数", "依赖深度", "影响评估", "链路状态", "最后更新"]
    REQUIRED_FIELDS = ["链路编号", "上游特征", "下游特征"]
    STATUS_ORDER = ["自动推导", "已确认", "环形告警", "已废弃"]
    ACTION_RULES = {"确认链路": "已确认", "标记环告": "环形告警", "废弃链路": "已废弃"}
    NEGATIVE_ACTIONS = []
