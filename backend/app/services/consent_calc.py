"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ConsentCalcService(BaseModuleService):
    MODULE = "consent_calc"
    ENTITY = "一致性报告"
    OPERATION_TERM = "计算"
    LIST_FIELDS = ["报告编号", "标注任务", "评估指标", "Kappa系数", "一致率", "争议项", "评估结论", "计算时间"]
    REQUIRED_FIELDS = ["报告编号", "标注任务", "评估指标"]
    STATUS_ORDER = ["待计算", "计算中", "已出分", "低于阈值"]
    ACTION_RULES = {"启动计算": "计算中", "确认结论": "已出分", "标记低分": "低于阈值"}
    NEGATIVE_ACTIONS = []
