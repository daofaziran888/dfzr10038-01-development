"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class FeatureMonService(BaseModuleService):
    MODULE = "feature_mon"
    ENTITY = "监控规则"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["规则编号", "目标特征", "监控类型", "基线分布", "漂移阈值", "告警级别", "最近检测", "漂移方向"]
    REQUIRED_FIELDS = ["规则编号", "目标特征", "监控类型"]
    STATUS_ORDER = ["草稿", "监控中", "分布漂移", "已停用"]
    ACTION_RULES = {"启用监控": "监控中", "确认漂移": "分布漂移", "停用监控": "已停用"}
    NEGATIVE_ACTIONS = ["停用监控"]
