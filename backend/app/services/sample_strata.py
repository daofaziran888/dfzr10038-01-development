"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class SampleStrataService(BaseModuleService):
    MODULE = "sample_strata"
    ENTITY = "分层策略"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["策略编号", "特征范围", "分层字段", "采样比例", "样本数量", "均衡算法", "覆盖检查", "最后采样"]
    REQUIRED_FIELDS = ["策略编号", "特征范围", "分层字段"]
    STATUS_ORDER = ["草稿", "采样中", "已出样", "覆盖不足"]
    ACTION_RULES = {"启动采样": "采样中", "确认出样": "已出样", "标记不足": "覆盖不足"}
    NEGATIVE_ACTIONS = []
