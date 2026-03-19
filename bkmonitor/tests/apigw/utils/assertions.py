"""
自定义断言工具

提供统一的 API 响应断言方法
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tests.apigw.models.base import ApiResponse


def assert_api_success(response: "ApiResponse", message: str = "") -> None:
    """
    断言 API 调用成功

    Args:
        response: API 响应对象
        message: 自定义错误消息
    """
    error_msg = message or f"API 调用失败: {response.message}"
    assert response.result is True, error_msg
    assert response.code == 200 or response.code == 0, f"响应码异常: {response.code}, {error_msg}"


def assert_api_error(
    response: "ApiResponse",
    expected_code: int | None = None,
    expected_message: str | None = None,
) -> None:
    """
    断言 API 调用返回错误

    Args:
        response: API 响应对象
        expected_code: 期望的错误码
        expected_message: 期望的错误消息（部分匹配）
    """
    assert response.result is False, f"期望 API 调用失败，但实际成功: {response.data}"

    if expected_code is not None:
        assert response.code == expected_code, f"错误码不匹配: 期望 {expected_code}, 实际 {response.code}"

    if expected_message is not None:
        assert expected_message in response.message, (
            f"错误消息不匹配: 期望包含 '{expected_message}', 实际 '{response.message}'"
        )


def assert_data_contains(data: dict[str, Any], expected: dict[str, Any], message: str = "") -> None:
    """
    断言数据包含期望的键值对

    Args:
        data: 实际数据
        expected: 期望的键值对
        message: 自定义错误消息
    """
    for key, value in expected.items():
        assert key in data, f"{message}数据缺少字段: {key}"
        assert data[key] == value, f"{message}字段 {key} 不匹配: 期望 {value}, 实际 {data[key]}"


def assert_list_contains_item(
    items: list[dict[str, Any]],
    match_field: str,
    match_value: Any,
    message: str = "",
) -> dict[str, Any]:
    """
    断言列表中包含指定项

    Args:
        items: 数据列表
        match_field: 匹配字段名
        match_value: 匹配字段值
        message: 自定义错误消息

    Returns:
        匹配到的项
    """
    for item in items:
        if item.get(match_field) == match_value:
            return item
    raise AssertionError(f"{message}列表中未找到 {match_field}={match_value} 的项")


def assert_list_not_contains_item(
    items: list[dict[str, Any]],
    match_field: str,
    match_value: Any,
    message: str = "",
) -> None:
    """
    断言列表中不包含指定项

    Args:
        items: 数据列表
        match_field: 匹配字段名
        match_value: 匹配字段值
        message: 自定义错误消息
    """
    for item in items:
        if item.get(match_field) == match_value:
            raise AssertionError(f"{message}列表中不应包含 {match_field}={match_value} 的项")
