"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class BackfillJobService(BaseModuleService):
    MODULE = "backfill_job"
    ENTITY = "回溯任务"
    OPERATION_TERM = "计算"
    LIST_FIELDS = ["任务编号", "目标特征", "起始日期", "截止日期", "回溯模式", "并行度", "当前进度", "数据行数"]
    REQUIRED_FIELDS = ["任务编号", "目标特征", "起始日期"]
    STATUS_ORDER = ["待执行", "回溯中", "已完成", "部分缺失"]
    ACTION_RULES = {"启动回溯": "回溯中", "暂停回溯": "已完成", "标记缺失": "部分缺失"}
    NEGATIVE_ACTIONS = []
