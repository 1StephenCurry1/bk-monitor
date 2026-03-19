"""
基础 API 客户端

提供统一的 HTTP 请求封装，支持认证、重试、错误处理
"""

import json
import logging
import time
from typing import Any, TypeVar
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from tests.apigw.models.base import (
    ApiAuthenticationError,
    ApiConnectionError,
    ApiError,
    ApiResponse,
    ApiTimeoutError,
)
from tests.apigw.utils.config_loader import Settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseApiClient:
    """
    基础 API 客户端

    提供统一的 HTTP 请求封装：
    - 自动认证处理（JWT Token 或 App Code/Secret）
    - 请求重试机制
    - 错误处理和异常封装
    - 请求/响应日志记录
    """

    def __init__(self, settings: Settings) -> None:
        """
        初始化客户端

        Args:
            settings: 全局配置对象
        """
        self.settings = settings
        self.base_url = settings.api_base_url
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """创建 HTTP Session，配置重试策略"""
        session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=self.settings.api.retry_count,
            backoff_factor=self.settings.api.retry_interval,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_auth_headers(self) -> dict[str, str]:
        """
        获取认证请求头

        蓝鲸 API 网关使用 X-Bkapi-Authorization 头传递认证信息
        """
        headers: dict[str, str] = {}

        auth_info: dict[str, str] = {}
        if self.settings.auth.app_code:
            auth_info["bk_app_code"] = self.settings.auth.app_code
        if self.settings.auth.app_secret:
            auth_info["bk_app_secret"] = self.settings.auth.app_secret

        if auth_info:
            headers["X-Bkapi-Authorization"] = json.dumps(auth_info)

        return headers

    def _get_auth_params(self) -> dict[str, str]:
        """获取认证请求参数（保留用于兼容其他场景）"""
        return {}

    def _build_url(self, endpoint: str) -> str:
        """构建完整的请求 URL"""
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]
        return urljoin(self.base_url + "/", endpoint)

    def _log_request(self, method: str, url: str, **kwargs: Any) -> None:
        """记录请求日志"""
        if self.settings.logging.verbose:
            logger.info(f"Request: {method} {url}")
            if kwargs.get("json"):
                logger.info(f"Request Body: {kwargs['json']}")
            if kwargs.get("params"):
                logger.info(f"Request Params: {kwargs['params']}")

    def _log_response(self, response: requests.Response, elapsed: float) -> None:
        """记录响应日志"""
        if self.settings.logging.verbose:
            logger.info(f"Response: {response.status_code} ({elapsed:.2f}s)")
            logger.info(f"Response Body: {response.text[:1000]}")

    def _handle_response(self, response: requests.Response) -> ApiResponse[Any]:
        """
        处理响应，转换为统一的 ApiResponse 格式

        Args:
            response: HTTP 响应对象

        Returns:
            ApiResponse 对象

        Raises:
            ApiAuthenticationError: 认证失败
            ApiError: 其他 API 错误
        """
        try:
            data = response.json()
        except ValueError:
            # 响应不是 JSON 格式
            if response.status_code == 401:
                raise ApiAuthenticationError("认证失败", code=401)
            raise ApiError(f"响应解析失败: {response.text[:200]}", code=response.status_code)

        # 构建 ApiResponse
        api_response = ApiResponse[Any](
            result=data.get("result", response.status_code == 200),
            code=data.get("code", response.status_code),
            message=data.get("message", ""),
            data=data.get("data"),
        )

        # 检查认证错误
        if response.status_code == 401 or api_response.code == 401:
            raise ApiAuthenticationError(api_response.message or "认证失败", code=401, response=api_response)

        return api_response

    def request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> ApiResponse[Any]:
        """
        发送 HTTP 请求

        Args:
            method: HTTP 方法 (GET, POST, PUT, PATCH, DELETE)
            endpoint: API 端点路径
            params: URL 查询参数
            json: JSON 请求体
            data: 表单数据
            headers: 额外的请求头
            **kwargs: 其他 requests 参数

        Returns:
            ApiResponse 对象

        Raises:
            ApiConnectionError: 连接失败
            ApiTimeoutError: 请求超时
            ApiAuthenticationError: 认证失败
            ApiError: 其他 API 错误
        """
        url = self._build_url(endpoint)

        # 合并认证信息
        request_headers = self._get_auth_headers()
        if headers:
            request_headers.update(headers)

        request_params = self._get_auth_params()
        if params:
            request_params.update(params)

        # 设置超时
        kwargs.setdefault("timeout", self.settings.api.timeout)

        self._log_request(method, url, params=request_params, json=json, data=data)

        start_time = time.time()
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=request_params,
                json=json,
                data=data,
                headers=request_headers,
                **kwargs,
            )
        except requests.exceptions.ConnectionError as e:
            raise ApiConnectionError(f"连接失败: {e}") from e
        except requests.exceptions.Timeout as e:
            raise ApiTimeoutError(f"请求超时: {e}") from e
        except requests.exceptions.RequestException as e:
            raise ApiError(f"请求失败: {e}") from e

        elapsed = time.time() - start_time
        self._log_response(response, elapsed)

        return self._handle_response(response)

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ApiResponse[Any]:
        """发送 GET 请求"""
        return self.request("GET", endpoint, params=params, **kwargs)

    def post(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ApiResponse[Any]:
        """发送 POST 请求"""
        return self.request("POST", endpoint, json=json, data=data, params=params, **kwargs)

    def put(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ApiResponse[Any]:
        """发送 PUT 请求"""
        return self.request("PUT", endpoint, json=json, params=params, **kwargs)

    def patch(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ApiResponse[Any]:
        """发送 PATCH 请求"""
        return self.request("PATCH", endpoint, json=json, params=params, **kwargs)

    def delete(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ApiResponse[Any]:
        """发送 DELETE 请求"""
        return self.request("DELETE", endpoint, params=params, json=json, **kwargs)
