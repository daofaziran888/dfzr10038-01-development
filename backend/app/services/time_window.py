"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class TimeWindowService(BaseModuleService):
    MODULE = "time_window"
    ENTITY = "窗口模板"
    OPERATION_TERM = "计算"
    LIST_FIELDS = ["模板编号", "窗口类型", "窗口宽度", "滑动步长", "对齐基准", "缺值填充", "特征列表", "最近计算"]
    REQUIRED_FIELDS = ["模板编号", "窗口类型", "窗口宽度"]
    STATUS_ORDER = ["草稿", "计算中", "窗口关闭", "已废弃"]
    ACTION_RULES = {"启动计算": "计算中", "关闭窗口": "窗口关闭", "废弃模板": "已废弃"}
    NEGATIVE_ACTIONS = []
