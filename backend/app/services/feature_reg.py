"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class FeatureRegService(BaseModuleService):
    MODULE = "feature_reg"
    ENTITY = "特征定义"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["特征编号", "特征名称", "数据类型", "业务域", "数据来源", "更新频率", "负责人", "注册时间"]
    REQUIRED_FIELDS = ["特征编号", "特征名称", "数据类型"]
    STATUS_ORDER = ["草稿", "已注册", "待更新", "已废弃"]
    ACTION_RULES = {"审核注册": "已注册", "提交更新": "待更新", "废弃特征": "已废弃"}
    NEGATIVE_ACTIONS = []
