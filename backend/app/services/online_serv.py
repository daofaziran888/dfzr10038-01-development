"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class OnlineServService(BaseModuleService):
    MODULE = "online_serv"
    ENTITY = "服务端点"
    OPERATION_TERM = "查询"
    LIST_FIELDS = ["端点编号", "特征列表", "QPS上限", "延迟SLA", "缓存策略", "热加载", "服务端口", "运行状态"]
    REQUIRED_FIELDS = ["端点编号", "特征列表", "QPS上限"]
    STATUS_ORDER = ["待部署", "运行中", "降级中", "已停用"]
    ACTION_RULES = {"部署服务": "运行中", "降级服务": "降级中", "停用服务": "已停用"}
    NEGATIVE_ACTIONS = ["停用服务"]
