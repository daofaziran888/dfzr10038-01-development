"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class DataSplitService(BaseModuleService):
    MODULE = "data_split"
    ENTITY = "切分配置"
    OPERATION_TERM = "切分"
    LIST_FIELDS = ["配置编号", "数据集", "切分方式", "训练比例", "验证比例", "测试比例", "切分种子", "切分时间"]
    REQUIRED_FIELDS = ["配置编号", "数据集", "切分方式"]
    STATUS_ORDER = ["草稿", "切分中", "已切分", "切分异常"]
    ACTION_RULES = {"启动切分": "切分中", "确认切分": "已切分", "标记异常": "切分异常"}
    NEGATIVE_ACTIONS = []
