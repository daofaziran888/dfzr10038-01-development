"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class BatchLoadService(BaseModuleService):
    MODULE = "batch_load"
    ENTITY = "接入任务"
    OPERATION_TERM = "接入"
    LIST_FIELDS = ["任务编号", "数据源", "目标特征", "映射配置", "校验规则", "接入行数", "拒绝行数", "接入时间"]
    REQUIRED_FIELDS = ["任务编号", "数据源", "目标特征"]
    STATUS_ORDER = ["待执行", "接入中", "已完成", "部分拒绝"]
    ACTION_RULES = {"启动接入": "接入中", "暂停接入": "已完成", "标记拒绝": "部分拒绝"}
    NEGATIVE_ACTIONS = []
