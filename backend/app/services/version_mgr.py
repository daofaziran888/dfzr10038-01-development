"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class VersionMgrService(BaseModuleService):
    MODULE = "version_mgr"
    ENTITY = "特征版本"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["版本编号", "关联特征", "版本标签", "计算逻辑", "数据窗口", "变更原因", "灰度比例", "版本状态"]
    REQUIRED_FIELDS = ["版本编号", "关联特征", "版本标签"]
    STATUS_ORDER = ["草稿", "灰度中", "全量生效", "已回滚"]
    ACTION_RULES = {"灰度发布": "灰度中", "全量切换": "全量生效", "回滚版本": "已回滚"}
    NEGATIVE_ACTIONS = ["回滚版本"]
