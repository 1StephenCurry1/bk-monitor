"""工具模块"""

from tests.apigw.utils.assertions import (
    assert_api_error,
    assert_api_success,
    assert_data_contains,
    assert_list_contains_item,
    assert_list_not_contains_item,
)
from tests.apigw.utils.config_loader import Settings, load_settings
from tests.apigw.utils.response_validator import (
    # 预置规则
    CommonRules,
    # 核心类
    FieldRule,
    ResponseValidator,
    ValidationResult,
    # 断言方法
    assert_data_valid,
    assert_response_valid,
    # 快捷方法
    expect_types,
    expect_values,
    field_equals,
    field_exists,
    field_in,
    field_matches,
    field_not_empty,
    field_type_is,
    require_fields,
)

__all__ = [
    # 配置
    "Settings",
    "load_settings",
    # 基础断言
    "assert_api_success",
    "assert_api_error",
    "assert_data_contains",
    "assert_list_contains_item",
    "assert_list_not_contains_item",
    # 响应校验器
    "FieldRule",
    "ValidationResult",
    "ResponseValidator",
    "require_fields",
    "expect_values",
    "expect_types",
    "field_exists",
    "field_equals",
    "field_type_is",
    "field_matches",
    "field_in",
    "field_not_empty",
    "assert_response_valid",
    "assert_data_valid",
    "CommonRules",
]
