"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class LabelReviewService(BaseModuleService):
    MODULE = "label_review"
    ENTITY = "审核批次"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["批次编号", "标注任务", "审核人", "样本数量", "通过数量", "驳回数量", "一致率", "审核时间"]
    REQUIRED_FIELDS = ["批次编号", "标注任务", "审核人"]
    STATUS_ORDER = ["待审核", "审核中", "已通过", "返修中"]
    ACTION_RULES = {"提交审核": "审核中", "确认通过": "已通过", "发起返修": "返修中"}
    NEGATIVE_ACTIONS = []
