"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class QualityRuleService(BaseModuleService):
    MODULE = "quality_rule"
    ENTITY = "质量检查"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["规则编号", "目标特征", "检查类型", "空值阈值", "异常值阈值", "阻断级别", "采样比例", "最近检查"]
    REQUIRED_FIELDS = ["规则编号", "目标特征", "检查类型"]
    STATUS_ORDER = ["草稿", "监控中", "已阻断", "已暂停"]
    ACTION_RULES = {"启用监控": "监控中", "确认阻断": "已阻断", "暂停规则": "已暂停"}
    NEGATIVE_ACTIONS = []
