"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ReportTaskService(BaseModuleService):
    MODULE = "report_task"
    ENTITY = "分析报表"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["报告编号", "报告类型", "特征范围", "统计周期", "图表配置", "输出格式", "分发列表", "最近生成"]
    REQUIRED_FIELDS = ["报告编号", "报告类型", "特征范围"]
    STATUS_ORDER = ["草稿", "生成中", "已生成", "生成失败"]
    ACTION_RULES = {"启动生成": "生成中", "中止生成": "已生成", "标记失败": "生成失败"}
    NEGATIVE_ACTIONS = []
