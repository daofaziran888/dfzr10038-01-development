"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class DeriveRuleService(BaseModuleService):
    MODULE = "derive_rule"
    ENTITY = "衍生规则"
    OPERATION_TERM = "计算"
    LIST_FIELDS = ["规则编号", "输入特征", "衍生函数", "输出特征", "计算粒度", "依赖表", "刷新策略", "最近产出"]
    REQUIRED_FIELDS = ["规则编号", "输入特征", "衍生函数"]
    STATUS_ORDER = ["草稿", "生效中", "计算异常", "已停用"]
    ACTION_RULES = {"启效规则": "生效中", "标记异常": "计算异常", "停用规则": "已停用"}
    NEGATIVE_ACTIONS = ["停用规则"]
