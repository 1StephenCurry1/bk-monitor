"""
告警策略模块（Alarm Strategy）API 响应校验规则

基于实际 APIGW 接口返回结构定义，严格校验所有字段。

接口列表（共 9 个，全部可用 ✅）：
基础接口:
- search_alarm_strategy: 查询告警策略列表
- save_alarm_strategy: 保存告警策略
- switch_alarm_strategy: 启停告警策略
- delete_alarm_strategy: 删除告警策略
- search_alarm_strategy_without_biz: 查询全业务告警策略
- switch_alarm_strategy_by_labels: 根据标签批量启停策略

V3 迁移接口:
- search_alarm_strategy_v3: 查询告警策略列表（迁移版）
- save_alarm_strategy_v3: 保存告警策略（迁移版）
- delete_alarm_strategy_v3: 删除告警策略（迁移版）

APIGW URL 路径映射:
- 基础接口: /app/alarm_strategy/{action}/
- V3 迁移接口: /app/alarm_strategy/{action}/v3/
"""

from __future__ import annotations

from tests.apigw.utils.response_validator import (
    FieldRule,
    expect_values,
)


class AlarmStrategyRules:
    """
    告警策略模块专用校验规则集合

    所有规则基于实际 API 返回结构严格定义，确保：
    1. 字段一定存在
    2. 字段类型正确
    3. 可预测的值符合预期

    Example:
        >>> from tests.apigw.rules import AlarmStrategyRules
        >>> rules = AlarmStrategyRules.search_response()
        >>> # 验证搜索接口返回
    """

    # ==================== 枚举值定义 ====================

    # 有效的策略版本
    VALID_VERSIONS: list[str] = ["v2"]

    # ==================== Search 接口规则 ====================

    @staticmethod
    def search_response() -> list[FieldRule]:
        """
        search_alarm_strategy 响应校验规则

        严格校验 data 下的 11 个字段全部存在且类型正确
        """
        return [
            # === 基础响应结构 ===
            FieldRule(path="$.result", required=True, expected_type=bool),
            FieldRule(
                path="$.result",
                validator=lambda x: x is True,
                error_message="result 必须为 true",
            ),
            FieldRule(path="$.code", required=True, expected_type=int),
            FieldRule(
                path="$.code",
                validator=lambda x: x == 200,
                error_message="code 必须为 200",
            ),
            FieldRule(path="$.message", required=True, expected_type=str),
            FieldRule(path="$.data", required=True, expected_type=dict),
            # === data 内部结构 - 11 个字段全部必须存在 ===
            # 核心业务数据
            FieldRule(path="$.data.scenario_list", required=True, expected_type=list),
            FieldRule(path="$.data.strategy_config_list", required=True, expected_type=list),
            FieldRule(path="$.data.total", required=True, expected_type=int),
            # 筛选器相关列表
            FieldRule(path="$.data.data_source_list", required=True, expected_type=list),
            FieldRule(path="$.data.strategy_label_list", required=True, expected_type=list),
            FieldRule(path="$.data.strategy_status_list", required=True, expected_type=list),
            FieldRule(path="$.data.user_group_list", required=True, expected_type=list),
            FieldRule(path="$.data.action_config_list", required=True, expected_type=list),
            FieldRule(path="$.data.alert_level_list", required=True, expected_type=list),
            FieldRule(path="$.data.invalid_type_list", required=True, expected_type=list),
            FieldRule(path="$.data.algorithm_type_list", required=True, expected_type=list),
            # === 策略状态列表必须包含 5 种状态 ===
            FieldRule(
                path="$.data.strategy_status_list",
                validator=lambda x: len(x) == 5,
                error_message="strategy_status_list 必须包含 5 种状态",
            ),
            # === 告警级别列表必须包含 3 种级别 ===
            FieldRule(
                path="$.data.alert_level_list",
                validator=lambda x: len(x) == 3,
                error_message="alert_level_list 必须包含 3 种级别",
            ),
            # === 场景列表必须包含 11 种场景 ===
            FieldRule(
                path="$.data.scenario_list",
                validator=lambda x: len(x) == 11,
                error_message="scenario_list 必须包含 11 种场景",
            ),
        ]

    # ==================== Save 接口规则 ====================

    @staticmethod
    def save_response() -> list[FieldRule]:
        """
        save_alarm_strategy 响应校验规则

        返回 25 个字段，部分字段可能为 None 或空字符串
        """
        return [
            # === 基础响应结构 ===
            FieldRule(path="$.result", required=True, expected_type=bool),
            FieldRule(
                path="$.result",
                validator=lambda x: x is True,
                error_message="result 必须为 true",
            ),
            FieldRule(path="$.code", required=True, expected_type=int),
            FieldRule(
                path="$.code",
                validator=lambda x: x == 200,
                error_message="code 必须为 200",
            ),
            FieldRule(path="$.message", required=True, expected_type=str),
            FieldRule(path="$.data", required=True, expected_type=dict),
            # === 核心标识字段（必须有值） ===
            FieldRule(path="$.data.id", required=True, expected_type=int),
            FieldRule(
                path="$.data.id",
                validator=lambda x: x > 0,
                error_message="策略 ID 必须 > 0",
            ),
            FieldRule(path="$.data.version", required=True, expected_type=str),
            FieldRule(
                path="$.data.version",
                validator=lambda x: x in AlarmStrategyRules.VALID_VERSIONS,
                error_message=f"version 必须是 {AlarmStrategyRules.VALID_VERSIONS} 之一",
            ),
            FieldRule(path="$.data.bk_biz_id", required=True, expected_type=int),
            FieldRule(path="$.data.name", required=True, expected_type=str),
            FieldRule(path="$.data.source", required=True, expected_type=str),
            FieldRule(path="$.data.scenario", required=True, expected_type=str),
            FieldRule(path="$.data.type", required=True, expected_type=str),
            # === 配置结构 ===
            FieldRule(path="$.data.items", required=True, expected_type=list),
            FieldRule(path="$.data.detects", required=True, expected_type=list),
            FieldRule(path="$.data.actions", required=True, expected_type=list),
            FieldRule(path="$.data.notice", required=True, expected_type=dict),
            # === 状态 ===
            FieldRule(path="$.data.is_enabled", required=True, expected_type=bool),
            FieldRule(path="$.data.is_invalid", required=True, expected_type=bool),
            FieldRule(path="$.data.invalid_type", required=True, expected_type=str),
            # === 时间 ===
            FieldRule(path="$.data.update_time", required=True, expected_type=str),
            FieldRule(path="$.data.create_time", required=True, expected_type=str),
            # === 用户（可能为空字符串） ===
            FieldRule(path="$.data.update_user", required=True, expected_type=str),
            FieldRule(path="$.data.create_user", required=True, expected_type=str),
            # === 标签 ===
            FieldRule(path="$.data.labels", required=True, expected_type=list),
            # === 路径（可能为空字符串） ===
            FieldRule(path="$.data.app", required=True, expected_type=str),
            FieldRule(path="$.data.path", required=True, expected_type=str),
            # === 优先级（可能为 None） ===
            FieldRule(path="$.data.priority", required=True),  # 可能是 int 或 None
            FieldRule(path="$.data.priority_group_key", required=True, expected_type=str),
            # === 权限 ===
            FieldRule(path="$.data.edit_allowed", required=True, expected_type=bool),
            # === 指标类型 ===
            FieldRule(path="$.data.metric_type", required=True, expected_type=str),
        ]

    @staticmethod
    def save_response_with_values(
        expected_name: str,
        expected_bk_biz_id: int,
        expected_scenario: str = "os",
        expected_is_enabled: bool = False,
    ) -> list[FieldRule]:
        """
        save 响应校验规则（带精确值校验）
        """
        rules = AlarmStrategyRules.save_response()
        rules.extend(
            expect_values(
                {
                    "$.data.name": expected_name,
                    "$.data.bk_biz_id": expected_bk_biz_id,
                    "$.data.scenario": expected_scenario,
                    "$.data.is_enabled": expected_is_enabled,
                }
            )
        )
        return rules

    # ==================== Switch 接口规则 ====================

    @staticmethod
    def switch_response() -> list[FieldRule]:
        """
        switch_alarm_strategy 响应校验规则

        实际结构：
        {
            "result": true,
            "code": 200,
            "message": "OK",
            "data": {
                "ids": [int, ...]
            }
        }
        """
        return [
            FieldRule(path="$.result", required=True, expected_type=bool),
            FieldRule(
                path="$.result",
                validator=lambda x: x is True,
                error_message="result 必须为 true",
            ),
            FieldRule(path="$.code", required=True, expected_type=int),
            FieldRule(
                path="$.code",
                validator=lambda x: x == 200,
                error_message="code 必须为 200",
            ),
            FieldRule(path="$.message", required=True, expected_type=str),
            FieldRule(path="$.data", required=True, expected_type=dict),
            FieldRule(path="$.data.ids", required=True, expected_type=list),
        ]

    @staticmethod
    def switch_response_with_ids(expected_ids: list[int]) -> list[FieldRule]:
        """
        switch 响应校验规则（验证返回的 ID 列表）
        """
        rules = AlarmStrategyRules.switch_response()
        rules.append(
            FieldRule(
                path="$.data.ids",
                validator=lambda x: set(x) == set(expected_ids),
                error_message=f"返回的 ID 列表应为 {expected_ids}",
            )
        )
        return rules

    # ==================== Delete 接口规则 ====================

    @staticmethod
    def delete_response() -> list[FieldRule]:
        """
        delete_alarm_strategy 响应校验规则

        实际结构：
        {
            "result": true,
            "code": 200,
            "message": "OK",
            "data": null
        }
        """
        return [
            FieldRule(path="$.result", required=True, expected_type=bool),
            FieldRule(
                path="$.result",
                validator=lambda x: x is True,
                error_message="result 必须为 true",
            ),
            FieldRule(path="$.code", required=True, expected_type=int),
            FieldRule(
                path="$.code",
                validator=lambda x: x == 200,
                error_message="code 必须为 200",
            ),
            FieldRule(path="$.message", required=True, expected_type=str),
            # data 为 null，不需要校验
        ]

    # ==================== Search Without Biz 接口规则 ====================

    @staticmethod
    def search_without_biz_response() -> list[FieldRule]:
        """
        search_alarm_strategy_without_biz 响应校验规则

        端点: POST /app/alarm_strategy/search_without_biz/

        响应结构：
        {
            "result": true,
            "code": 200,
            "message": "OK",
            "data": {
                "list": [...],   # 策略列表
                "total": int     # 总数
            }
        }
        """
        return [
            FieldRule(path="$.result", required=True, expected_type=bool),
            FieldRule(
                path="$.result",
                validator=lambda x: x is True,
                error_message="result 必须为 true",
            ),
            FieldRule(path="$.code", required=True, expected_type=int),
            FieldRule(
                path="$.code",
                validator=lambda x: x == 200,
                error_message="code 必须为 200",
            ),
            FieldRule(path="$.message", required=True, expected_type=str),
            FieldRule(path="$.data", required=True, expected_type=dict),
            FieldRule(path="$.data.list", required=True, expected_type=list),
            FieldRule(path="$.data.total", required=True, expected_type=int),
            FieldRule(
                path="$.data.total",
                validator=lambda x: x >= 0,
                error_message="total 必须 >= 0",
            ),
        ]

    # ==================== Switch By Labels 接口规则 ====================

    @staticmethod
    def switch_by_labels_response() -> list[FieldRule]:
        """
        switch_alarm_strategy_by_labels 响应校验规则

        端点: POST /app/alarm_strategy/switch_by_labels/

        响应结构：
        {
            "result": true,
            "code": 200,
            "message": "OK",
            "data": [int, ...]  # 受影响的策略 ID 列表
        }
        """
        return [
            FieldRule(path="$.result", required=True, expected_type=bool),
            FieldRule(
                path="$.result",
                validator=lambda x: x is True,
                error_message="result 必须为 true",
            ),
            FieldRule(path="$.code", required=True, expected_type=int),
            FieldRule(
                path="$.code",
                validator=lambda x: x == 200,
                error_message="code 必须为 200",
            ),
            FieldRule(path="$.message", required=True, expected_type=str),
            FieldRule(path="$.data", required=True, expected_type=list),
        ]
