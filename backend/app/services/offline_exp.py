"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class OfflineExpService(BaseModuleService):
    MODULE = "offline_exp"
    ENTITY = "导出管道"
    OPERATION_TERM = "导出"
    LIST_FIELDS = ["管道编号", "特征范围", "导出格式", "分区策略", "批次大小", "压缩方式", "目标地址", "最后导出"]
    REQUIRED_FIELDS = ["管道编号", "特征范围", "导出格式"]
    STATUS_ORDER = ["待执行", "导出中", "已完成", "导出异常"]
    ACTION_RULES = {"启动导出": "导出中", "暂停导出": "已完成", "标记异常": "导出异常"}
    NEGATIVE_ACTIONS = []
