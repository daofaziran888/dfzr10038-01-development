"""业务路由汇总：目录发布治理走专用路由，其余模块共用一套资源路由。"""
from __future__ import annotations

from app.routers import catalog_release, resource

# 固定前缀的目录发布治理路由必须排在动态 /{module} 资源路由之前。
ROUTERS = [catalog_release, resource]
