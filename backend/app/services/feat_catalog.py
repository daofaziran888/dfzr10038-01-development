"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class FeatCatalogService(BaseModuleService):
    MODULE = "feat_catalog"
    ENTITY = "目录索引"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["索引编号", "目录名称", "父目录", "目录层级", "关联特征", "目录描述", "排序权重", "创建时间"]
    REQUIRED_FIELDS = ["索引编号", "目录名称", "父目录"]
    STATUS_ORDER = ["草稿", "已发布", "重构中", "已归档"]
    ACTION_RULES = {"发布目录": "已发布", "重构层级": "重构中", "归档目录": "已归档"}
    NEGATIVE_ACTIONS = []
