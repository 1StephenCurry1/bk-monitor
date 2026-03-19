"""
基础数据模型

定义 API 响应的通用数据结构
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    API 响应通用模型

    蓝鲸监控 API 标准响应格式：
    {
        "result": true/false,
        "code": 200,
        "message": "success",
        "data": {...}
    }
    """

    result: bool = Field(description="请求是否成功")
    code: int = Field(default=200, description="响应码")
    message: str = Field(default="", description="响应消息")
    data: T | None = Field(default=None, description="响应数据")

    @property
    def is_success(self) -> bool:
        """判断请求是否成功"""
        return self.result is True


class PaginatedData(BaseModel, Generic[T]):
    """分页数据模型"""

    count: int = Field(default=0, description="总数")
    results: list[T] = Field(default_factory=list, description="数据列表")
    # 兼容不同的分页字段名
    total: int | None = Field(default=None, description="总数（备用字段）")
    # 注意：使用 alias 处理 API 返回的 "list" 字段（避免与内置 list 冲突）
    data_list: list[T] | None = Field(default=None, alias="list", description="数据列表（备用字段）")

    @property
    def items(self) -> list[T]:
        """获取数据列表（兼容不同字段名）"""
        if self.results:
            return self.results
        if self.data_list:
            return self.data_list
        return []

    @property
    def total_count(self) -> int:
        """获取总数（兼容不同字段名）"""
        if self.count:
            return self.count
        if self.total:
            return self.total
        return len(self.items)


class PaginatedResponse(ApiResponse[PaginatedData[T]], Generic[T]):
    """分页响应模型"""

    pass


class ErrorDetail(BaseModel):
    """错误详情模型"""

    field: str = Field(default="", description="错误字段")
    message: str = Field(default="", description="错误消息")
    code: str = Field(default="", description="错误码")


class ApiError(Exception):
    """API 错误异常"""

    def __init__(
        self,
        message: str,
        code: int = -1,
        response: ApiResponse[Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.response = response
        super().__init__(message)

    def __str__(self) -> str:
        return f"ApiError(code={self.code}, message={self.message})"


class ApiConnectionError(ApiError):
    """API 连接错误"""

    pass


class ApiTimeoutError(ApiError):
    """API 超时错误"""

    pass


class ApiAuthenticationError(ApiError):
    """API 认证错误"""

    pass
