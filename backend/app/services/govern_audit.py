"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class GovernAuditService(BaseModuleService):
    MODULE = "govern_audit"
    ENTITY = "审计记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["记录编号", "审计对象", "审计类型", "检查结果", "问题项", "整改方案", "审计时间", "整改状态"]
    REQUIRED_FIELDS = ["记录编号", "审计对象", "审计类型"]
    STATUS_ORDER = ["待审计", "审计中", "已通过", "整改中"]
    ACTION_RULES = {"发起审计": "审计中", "确认通过": "已通过", "指派整改": "整改中"}
    NEGATIVE_ACTIONS = []
