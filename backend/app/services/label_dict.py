"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class LabelDictService(BaseModuleService):
    MODULE = "label_dict"
    ENTITY = "标注项"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["词典编号", "标签名称", "标签值", "标签层级", "描述说明", "互斥组", "适用场景", "使用次数"]
    REQUIRED_FIELDS = ["词典编号", "标签名称", "标签值"]
    STATUS_ORDER = ["草稿", "已发布", "已修订", "已废弃"]
    ACTION_RULES = {"发布标签": "已发布", "修订标签": "已修订", "废弃标签": "已废弃"}
    NEGATIVE_ACTIONS = []
