"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ScheduleJobService(BaseModuleService):
    MODULE = "schedule_job"
    ENTITY = "调度计划"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["计划编号", "任务类型", "关联对象", "Cron表达式", "时区设置", "依赖检查", "失败通知", "下次执行"]
    REQUIRED_FIELDS = ["计划编号", "任务类型", "关联对象"]
    STATUS_ORDER = ["待激活", "执行中", "已完成", "已停用"]
    ACTION_RULES = {"激活计划": "执行中", "立即执行": "已完成", "停用计划": "已停用"}
    NEGATIVE_ACTIONS = ["停用计划"]
