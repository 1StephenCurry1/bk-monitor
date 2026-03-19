"""数据模型模块"""

from tests.apigw.models.base import ApiResponse, PaginatedResponse
from tests.apigw.models.uptime_check import (
    UptimeCheckNodeCreate,
    UptimeCheckNodeUpdate,
    UptimeCheckTaskCreate,
    UptimeCheckTaskUpdate,
    UptimeCheckGroupCreate,
    UptimeCheckGroupUpdate,
)

__all__ = [
    "ApiResponse",
    "PaginatedResponse",
    "UptimeCheckNodeCreate",
    "UptimeCheckNodeUpdate",
    "UptimeCheckTaskCreate",
    "UptimeCheckTaskUpdate",
    "UptimeCheckGroupCreate",
    "UptimeCheckGroupUpdate",
]
