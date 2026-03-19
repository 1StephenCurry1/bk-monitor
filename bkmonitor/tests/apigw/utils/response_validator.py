"""
API 响应校验器

使用 JSONPath 进行灵活的响应数据校验，支持：
- 必填字段校验
- 精确值校验
- 类型校验
- 自定义校验函数
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from collections.abc import Callable

from jsonpath_ng import parse as jsonpath_parse
from jsonpath_ng.exceptions import JsonPathParserError

if TYPE_CHECKING:
    from tests.apigw.models.base import ApiResponse


@dataclass
class FieldRule:
    """
    字段校验规则

    Attributes:
        path: JSONPath 表达式，支持标准 JSONPath 语法
              示例: "$.data.id", "$.data.items[0].name", "$.data.config.url"
              也支持简化写法: "data.id" (会自动添加 $. 前缀)
        required: 字段是否必须存在，默认 True
        expected_value: 期望的精确值，None 表示不校验值（除非 _check_value=True）
        expected_type: 期望的类型，可以是单个类型或类型元组
        validator: 自定义校验函数，接收字段值，返回 bool
        error_message: 自定义错误消息

    Example:
        >>> # 必填字段
        >>> FieldRule("$.data.id", required=True)
        >>>
        >>> # 精确值校验
        >>> FieldRule("$.data.name", expected_value="test")
        >>>
        >>> # 类型校验
        >>> FieldRule("$.data.count", expected_type=int)
        >>>
        >>> # 自定义校验
        >>> FieldRule("$.data.status", validator=lambda x: x in ["enabled", "disabled"])
    """

    path: str
    required: bool = True
    expected_value: Any = field(default=None)
    expected_type: type | tuple[type, ...] | None = None
    validator: Callable[[Any], bool] | None = None
    error_message: str = ""

    # 标记是否需要校验值（区分 None 作为期望值的情况）
    _check_value: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        """初始化后处理：规范化 JSONPath"""
        # 规范化 JSONPath：确保以 $ 开头
        if not self.path.startswith("$"):
            self.path = f"$.{self.path}"


@dataclass
class ValidationError:
    """校验错误详情"""

    path: str
    message: str
    actual_value: Any = None
    expected_value: Any = None


class ValidationResult:
    """
    校验结果

    Example:
        >>> result = validator.validate(response, rules)
        >>> if not result.is_valid:
        ...     print(result.format_errors())
    """

    def __init__(self) -> None:
        self.errors: list[ValidationError] = []

    @property
    def is_valid(self) -> bool:
        """是否校验通过"""
        return len(self.errors) == 0

    def add_error(
        self,
        path: str,
        message: str,
        actual_value: Any = None,
        expected_value: Any = None,
    ) -> None:
        """添加校验错误"""
        self.errors.append(
            ValidationError(
                path=path,
                message=message,
                actual_value=actual_value,
                expected_value=expected_value,
            )
        )

    def format_errors(self) -> str:
        """格式化错误消息"""
        if not self.errors:
            return ""

        lines = ["响应校验失败:"]
        for i, error in enumerate(self.errors, 1):
            lines.append(f"  {i}. [{error.path}] {error.message}")
            if error.expected_value is not None:
                lines.append(f"      期望: {error.expected_value!r}")
            if error.actual_value is not None:
                lines.append(f"      实际: {error.actual_value!r}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"ValidationResult(is_valid={self.is_valid}, error_count={len(self.errors)})"


class ResponseValidator:
    """
    API 响应校验器

    使用 JSONPath 进行灵活的数据校验

    Example:
        >>> validator = ResponseValidator()
        >>> result = validator.validate(
        ...     response,
        ...     [
        ...         FieldRule("$.data.id", required=True, expected_type=int),
        ...         FieldRule("$.data.name", expected_value="test"),
        ...     ],
        ... )
        >>> if not result.is_valid:
        ...     print(result.format_errors())
    """

    def __init__(self) -> None:
        self._jsonpath_cache: dict[str, Any] = {}

    def _get_jsonpath(self, path: str) -> Any:
        """获取编译后的 JSONPath 表达式（带缓存）"""
        if path not in self._jsonpath_cache:
            try:
                self._jsonpath_cache[path] = jsonpath_parse(path)
            except JsonPathParserError as e:
                raise ValueError(f"无效的 JSONPath 表达式: {path}") from e
        return self._jsonpath_cache[path]

    def _extract_value(self, data: dict[str, Any], path: str) -> tuple[bool, Any]:
        """
        从数据中提取 JSONPath 对应的值

        Returns:
            (found, value): 是否找到字段，字段值
        """
        jsonpath_expr = self._get_jsonpath(path)
        matches = jsonpath_expr.find(data)

        if not matches:
            return False, None

        # 如果有多个匹配，返回列表；单个匹配返回值
        if len(matches) == 1:
            return True, matches[0].value
        return True, [match.value for match in matches]

    def _validate_rule(
        self,
        data: dict[str, Any],
        rule: FieldRule,
        result: ValidationResult,
    ) -> None:
        """验证单条规则"""
        found, value = self._extract_value(data, rule.path)

        # 1. 必填字段校验
        if rule.required and not found:
            error_msg = rule.error_message or "必填字段不存在"
            result.add_error(rule.path, error_msg)
            return

        # 字段不存在且非必填，跳过后续校验
        if not found:
            return

        # 2. 类型校验
        if rule.expected_type is not None:
            if not isinstance(value, rule.expected_type):
                expected_type_name = (
                    rule.expected_type.__name__ if isinstance(rule.expected_type, type) else str(rule.expected_type)
                )
                actual_type_name = type(value).__name__
                error_msg = rule.error_message or f"类型不匹配: 期望 {expected_type_name}, 实际 {actual_type_name}"
                result.add_error(rule.path, error_msg, actual_value=value)
                return

        # 3. 精确值校验
        if rule._check_value or rule.expected_value is not None:
            if value != rule.expected_value:
                error_msg = rule.error_message or "值不匹配"
                result.add_error(
                    rule.path,
                    error_msg,
                    actual_value=value,
                    expected_value=rule.expected_value,
                )
                return

        # 4. 自定义校验
        if rule.validator is not None:
            try:
                if not rule.validator(value):
                    error_msg = rule.error_message or "自定义校验失败"
                    result.add_error(rule.path, error_msg, actual_value=value)
            except Exception as e:
                result.add_error(rule.path, f"校验函数执行异常: {e}", actual_value=value)

    def validate(
        self,
        response: ApiResponse[Any],
        rules: list[FieldRule],
    ) -> ValidationResult:
        """
        校验 API 响应

        Args:
            response: API 响应对象
            rules: 校验规则列表

        Returns:
            ValidationResult: 校验结果
        """
        result = ValidationResult()

        # 构建完整的响应数据结构
        data = {
            "result": response.result,
            "code": response.code,
            "message": response.message,
            "data": response.data,
        }

        for rule in rules:
            self._validate_rule(data, rule, result)

        return result

    def validate_data(
        self,
        data: dict[str, Any],
        rules: list[FieldRule],
    ) -> ValidationResult:
        """
        校验任意字典数据

        Args:
            data: 待校验的字典数据
            rules: 校验规则列表

        Returns:
            ValidationResult: 校验结果
        """
        result = ValidationResult()

        for rule in rules:
            self._validate_rule(data, rule, result)

        return result


# ============== 快捷方法 ==============


def require_fields(paths: list[str]) -> list[FieldRule]:
    """
    创建必填字段规则列表

    Args:
        paths: JSONPath 路径列表

    Returns:
        FieldRule 列表

    Example:
        >>> rules = require_fields(["$.data.id", "$.data.create_time"])
    """
    return [FieldRule(path=path, required=True) for path in paths]


def expect_values(mapping: dict[str, Any]) -> list[FieldRule]:
    """
    创建精确值校验规则列表

    传入的参数值必须与响应中的值完全一致

    Args:
        mapping: JSONPath 到期望值的映射

    Returns:
        FieldRule 列表

    Example:
        >>> rules = expect_values(
        ...     {
        ...         "$.data.name": "test_node",
        ...         "$.data.ip": "10.0.0.1",
        ...     }
        ... )
    """
    rules = []
    for path, value in mapping.items():
        rule = FieldRule(path=path, expected_value=value)
        rule._check_value = True  # 标记需要校验值（支持 None 作为期望值）
        rules.append(rule)
    return rules


def expect_types(mapping: dict[str, type | tuple[type, ...]]) -> list[FieldRule]:
    """
    创建类型校验规则列表

    Args:
        mapping: JSONPath 到期望类型的映射

    Returns:
        FieldRule 列表

    Example:
        >>> rules = expect_types(
        ...     {
        ...         "$.data.id": int,
        ...         "$.data.name": str,
        ...         "$.data.count": (int, float),
        ...     }
        ... )
    """
    return [FieldRule(path=path, expected_type=expected_type) for path, expected_type in mapping.items()]


def field_exists(path: str) -> FieldRule:
    """
    创建字段存在性规则

    Example:
        >>> rule = field_exists("$.data.id")
    """
    return FieldRule(path=path, required=True)


def field_equals(path: str, value: Any) -> FieldRule:
    """
    创建字段值相等规则

    Example:
        >>> rule = field_equals("$.data.name", "test")
    """
    rule = FieldRule(path=path, expected_value=value)
    rule._check_value = True
    return rule


def field_type_is(path: str, expected_type: type | tuple[type, ...]) -> FieldRule:
    """
    创建字段类型规则

    Example:
        >>> rule = field_type_is("$.data.id", int)
    """
    return FieldRule(path=path, expected_type=expected_type)


def field_matches(
    path: str,
    validator: Callable[[Any], bool],
    error_message: str = "",
) -> FieldRule:
    """
    创建自定义校验规则

    Example:
        >>> rule = field_matches(
        ...     "$.data.status", lambda x: x in ["enabled", "disabled"], "状态必须是 enabled 或 disabled"
        ... )
    """
    return FieldRule(path=path, validator=validator, error_message=error_message)


def field_in(path: str, allowed_values: list[Any], error_message: str = "") -> FieldRule:
    """
    创建字段值在允许列表中的规则

    Example:
        >>> rule = field_in("$.data.protocol", ["HTTP", "TCP", "UDP", "ICMP"])
    """
    msg = error_message or f"值必须在 {allowed_values} 中"
    return FieldRule(
        path=path,
        validator=lambda x: x in allowed_values,
        error_message=msg,
    )


def field_not_empty(path: str) -> FieldRule:
    """
    创建字段非空规则（存在且不为空字符串/空列表/空字典）

    Example:
        >>> rule = field_not_empty("$.data.name")
    """
    return FieldRule(
        path=path,
        required=True,
        validator=lambda x: bool(x),
        error_message="字段不能为空",
    )


# ============== 断言方法 ==============


# 全局校验器实例
_default_validator = ResponseValidator()


def assert_response_valid(
    response: ApiResponse[Any],
    rules: list[FieldRule],
    message: str = "",
) -> None:
    """
    断言 API 响应符合校验规则

    Args:
        response: API 响应对象
        rules: 校验规则列表
        message: 自定义错误消息前缀

    Raises:
        AssertionError: 校验失败时抛出

    Example:
        >>> assert_response_valid(
        ...     response,
        ...     [
        ...         FieldRule("$.data.id", required=True, expected_type=int),
        ...         FieldRule("$.data.name", expected_value="test"),
        ...     ],
        ... )
    """
    result = _default_validator.validate(response, rules)

    if not result.is_valid:
        error_msg = f"{message}\n{result.format_errors()}" if message else result.format_errors()
        raise AssertionError(error_msg)


def assert_data_valid(
    data: dict[str, Any],
    rules: list[FieldRule],
    message: str = "",
) -> None:
    """
    断言字典数据符合校验规则

    Args:
        data: 待校验的字典数据
        rules: 校验规则列表
        message: 自定义错误消息前缀

    Raises:
        AssertionError: 校验失败时抛出

    Example:
        >>> assert_data_valid(
        ...     {"name": "test", "id": 1},
        ...     [
        ...         FieldRule("$.id", expected_type=int),
        ...         FieldRule("$.name", expected_value="test"),
        ...     ],
        ... )
    """
    result = _default_validator.validate_data(data, rules)

    if not result.is_valid:
        error_msg = f"{message}\n{result.format_errors()}" if message else result.format_errors()
        raise AssertionError(error_msg)


# ============== 预置校验规则 ==============


class CommonRules:
    """
    常用校验规则集合

    提供常见场景的预置规则，简化测试代码编写
    """

    @staticmethod
    def id_field(path: str = "$.data.id") -> FieldRule:
        """
        ID 字段规则：必填、整数类型

        Example:
            >>> rule = CommonRules.id_field()
            >>> # 或自定义路径
            >>> rule = CommonRules.id_field("$.data.node_id")
        """
        return FieldRule(path=path, required=True, expected_type=int)

    @staticmethod
    def timestamp_fields(
        create_path: str = "$.data.create_time",
        update_path: str = "$.data.update_time",
    ) -> list[FieldRule]:
        """
        时间戳字段规则：必填

        Example:
            >>> rules = CommonRules.timestamp_fields()
        """
        return [
            FieldRule(path=create_path, required=True),
            FieldRule(path=update_path, required=True),
        ]

    @staticmethod
    def crud_response(
        id_path: str = "$.data.id",
        create_time_path: str = "$.data.create_time",
        update_time_path: str = "$.data.update_time",
    ) -> list[FieldRule]:
        """
        CRUD 操作响应通用规则

        包含：id（必填整数）、create_time（必填）、update_time（必填）

        Example:
            >>> rules = CommonRules.crud_response()
        """
        return [
            FieldRule(path=id_path, required=True, expected_type=int),
            FieldRule(path=create_time_path, required=True),
            FieldRule(path=update_time_path, required=True),
        ]

    @staticmethod
    def success_response() -> list[FieldRule]:
        """
        成功响应通用规则

        Example:
            >>> rules = CommonRules.success_response()
        """
        return [
            FieldRule(path="$.result", expected_value=True),
            FieldRule(
                path="$.code",
                validator=lambda x: x in (0, 200),
                error_message="响应码必须是 0 或 200",
            ),
        ]

    @staticmethod
    def list_response(
        min_count: int = 0,
        data_path: str = "$.data",
    ) -> list[FieldRule]:
        """
        列表响应规则

        Args:
            min_count: 最小数量
            data_path: 数据路径

        Example:
            >>> rules = CommonRules.list_response(min_count=1)
        """
        return [
            FieldRule(
                path=data_path,
                required=True,
                expected_type=list,
            ),
            FieldRule(
                path=data_path,
                validator=lambda x: isinstance(x, list) and len(x) >= min_count,
                error_message=f"列表长度必须 >= {min_count}",
            ),
        ]

    @staticmethod
    def pagination_response() -> list[FieldRule]:
        """
        分页响应规则

        Example:
            >>> rules = CommonRules.pagination_response()
        """
        return [
            FieldRule(path="$.data.count", required=True, expected_type=int),
            FieldRule(path="$.data.results", required=True, expected_type=list),
        ]
