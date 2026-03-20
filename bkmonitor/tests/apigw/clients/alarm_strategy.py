"""
告警策略 API 客户端

提供告警策略的 CRUD 和开关操作

接口列表（共9个）：
- search_alarm_strategy: 查询告警策略列表
- search_alarm_strategy_v3: 查询告警策略列表（迁移版）
- search_alarm_strategy_without_biz: 查询全业务告警策略
- save_alarm_strategy: 保存告警策略
- save_alarm_strategy_v3: 保存告警策略（迁移版）
- switch_alarm_strategy: 启停告警策略
- switch_alarm_strategy_by_labels: 根据标签批量启停策略
- delete_alarm_strategy: 删除告警策略
- delete_alarm_strategy_v3: 删除告警策略（迁移版）

APIGW URL 映射：
- 基础接口: /app/alarm_strategy/xxx/
- V3迁移接口: /app/alarm_strategy/xxx/v3/
"""

from __future__ import annotations

from typing import Any

from tests.apigw.clients.base import BaseApiClient
from tests.apigw.models.alarm_strategy import (
    AlarmStrategyDelete,
    AlarmStrategyFactory,
    AlarmStrategySave,
    AlarmStrategySearch,
    AlarmStrategySearchWithoutBiz,
    AlarmStrategySwitch,
    AlarmStrategySwitchByLabels,
)
from tests.apigw.models.base import ApiResponse
from tests.apigw.utils.config_loader import Settings


class AlarmStrategyClient:
    """
    告警策略 API 客户端

    提供策略的搜索、创建、更新、删除、启停等操作

    Example:
        >>> from tests.apigw.clients.alarm_strategy import AlarmStrategyClient
        >>> from tests.apigw.utils.config_loader import load_settings
        >>> settings = load_settings(environment="paas3")
        >>> client = AlarmStrategyClient(settings)
        >>> # 使用 Model 查询
        >>> response = client.search(AlarmStrategySearch(bk_biz_id=2))
        >>> # 或使用简便方法
        >>> response = client.search_by_biz(bk_biz_id=2)
    """

    def __init__(self, settings: Settings) -> None:
        """
        初始化客户端

        Args:
            settings: 全局配置对象
        """
        self._client = BaseApiClient(settings)
        self.settings = settings
        self._base_path = "alarm_strategy"

    @property
    def bk_biz_id(self) -> int:
        """获取默认业务 ID"""
        return self.settings.biz.bk_biz_id

    # ==================== Search 接口 ====================

    def search(self, request: AlarmStrategySearch) -> ApiResponse[Any]:
        """
        查询告警策略列表

        端点: POST /app/alarm_strategy/search/
        Backend: /api/v4/alarm_strategy_v3/search/

        Args:
            request: 查询请求模型

        Returns:
            包含 scenario_list, strategy_config_list 等的响应
        """
        return self._client.post(f"{self._base_path}/search/", json=request.model_dump(exclude_none=True))

    def search_by_biz(
        self,
        bk_biz_id: int | None = None,
        page: int = 1,
        page_size: int = 10,
        conditions: list[dict[str, Any]] | None = None,
        order_by: str = "-update_time",
        scenario: list[str] | None = None,
        with_user_group: bool = True,
        with_user_group_detail: bool = False,
    ) -> ApiResponse[Any]:
        """
        查询告警策略列表（简便方法）

        Args:
            bk_biz_id: 业务 ID（可选，默认使用配置中的业务 ID）
            page: 页码
            page_size: 每页数量
            conditions: 过滤条件列表
            order_by: 排序字段
            scenario: 场景过滤
            with_user_group: 是否返回用户组信息
            with_user_group_detail: 是否返回用户组详情
        """
        request = AlarmStrategySearch(
            bk_biz_id=bk_biz_id or self.bk_biz_id,
            page=page,
            page_size=page_size,
            conditions=conditions or [],
            order_by=order_by,
            scenario=scenario,
            with_user_group=with_user_group,
            with_user_group_detail=with_user_group_detail,
        )
        return self.search(request)

    def search_v3(self, request: AlarmStrategySearch) -> ApiResponse[Any]:
        """
        查询告警策略列表（V3 迁移版）

        端点: POST /app/alarm_strategy/search/v3/
        Backend: /api/v4/alarm_strategy_v3/search/

        注意：此接口与 search 接口后端相同，仅 APIGW 路径不同
        """
        return self._client.post(f"{self._base_path}/search/v3/", json=request.model_dump(exclude_none=True))

    def search_v3_by_biz(
        self,
        bk_biz_id: int | None = None,
        page: int = 1,
        page_size: int = 10,
        conditions: list[dict[str, Any]] | None = None,
        order_by: str = "-update_time",
    ) -> ApiResponse[Any]:
        """查询告警策略列表（V3，简便方法）"""
        request = AlarmStrategySearch(
            bk_biz_id=bk_biz_id or self.bk_biz_id,
            page=page,
            page_size=page_size,
            conditions=conditions or [],
            order_by=order_by,
        )
        return self.search_v3(request)

    def search_without_biz(self, request: AlarmStrategySearchWithoutBiz | None = None) -> ApiResponse[Any]:
        """
        查询全业务告警策略

        端点: POST /app/alarm_strategy/search_without_biz/
        Backend: /api/v4/alarm_strategy_v3/search_without_biz/

        Args:
            request: 查询请求模型（可选，不传则使用默认值）

        Returns:
            包含 list, total 的响应
        """
        if request is None:
            request = AlarmStrategySearchWithoutBiz()
        return self._client.post(f"{self._base_path}/search_without_biz/", json=request.model_dump(exclude_none=True))

    # ==================== Save 接口 ====================

    def save(self, request: AlarmStrategySave) -> ApiResponse[Any]:
        """
        保存告警策略

        端点: POST /app/alarm_strategy/save/
        Backend: /api/v4/alarm_strategy_v3/save/

        Args:
            request: 保存请求模型

        Returns:
            包含完整策略配置的响应
        """
        return self._client.post(f"{self._base_path}/save/", json=request.model_dump(exclude_none=True))

    def save_v3(self, request: AlarmStrategySave) -> ApiResponse[Any]:
        """
        保存告警策略（V3 迁移版）

        端点: POST /app/alarm_strategy/save/v3/
        Backend: /api/v4/alarm_strategy_v3/save/
        """
        return self._client.post(f"{self._base_path}/save/v3/", json=request.model_dump(exclude_none=True))

    def save_raw(self, strategy_config: dict[str, Any]) -> ApiResponse[Any]:
        """
        保存告警策略（原始请求，不做参数校验）

        用于测试边界条件或特殊场景

        Args:
            strategy_config: 完整的策略配置字典
        """
        return self._client.post(f"{self._base_path}/save/", json=strategy_config)

    def save_raw_v3(self, strategy_config: dict[str, Any]) -> ApiResponse[Any]:
        """保存告警策略（V3，原始请求）"""
        return self._client.post(f"{self._base_path}/save/v3/", json=strategy_config)

    def create_cpu_strategy(
        self,
        name: str,
        bk_biz_id: int | None = None,
        threshold: int | float = 90,
        is_enabled: bool = False,
        labels: list[str] | None = None,
    ) -> ApiResponse[Any]:
        """
        创建 CPU 使用率告警策略（便捷方法）

        Args:
            name: 策略名称
            bk_biz_id: 业务 ID
            threshold: CPU 阈值
            is_enabled: 是否启用
            labels: 标签列表
        """
        request = AlarmStrategyFactory.cpu_usage_strategy(
            bk_biz_id=bk_biz_id or self.bk_biz_id,
            name=name,
            threshold=threshold,
            is_enabled=is_enabled,
            labels=labels,
        )
        return self.save(request)

    # ==================== Update 接口 ====================

    def update(self, request: AlarmStrategySave) -> ApiResponse[Any]:
        """
        更新告警策略

        端点: POST /app/alarm_strategy/save/
        Backend: /api/v4/alarm_strategy_v3/save/

        注意：更新时 request.id 必须存在

        Args:
            request: 更新请求模型（必须包含 id）

        Returns:
            包含完整策略配置的响应
        """
        if request.id is None:
            raise ValueError("更新策略时必须提供 id")
        return self._client.post(f"{self._base_path}/save/", json=request.model_dump(exclude_none=True))

    def update_v3(self, request: AlarmStrategySave) -> ApiResponse[Any]:
        """更新告警策略（V3 迁移版）"""
        if request.id is None:
            raise ValueError("更新策略时必须提供 id")
        return self._client.post(f"{self._base_path}/save/v3/", json=request.model_dump(exclude_none=True))

    # ==================== Switch 接口 ====================

    def switch(self, request: AlarmStrategySwitch) -> ApiResponse[Any]:
        """
        启停告警策略

        端点: POST /app/alarm_strategy/switch/
        Backend: /api/v4/alarm_strategy/switch/ (V1 版本)

        Args:
            request: 启停请求模型

        Returns:
            包含 ids 列表的响应
        """
        return self._client.post(f"{self._base_path}/switch/", json=request.model_dump())

    def switch_by_ids(
        self,
        ids: list[int],
        is_enabled: bool,
        bk_biz_id: int | None = None,
    ) -> ApiResponse[Any]:
        """
        启停告警策略（简便方法）

        Args:
            ids: 策略 ID 列表
            is_enabled: 是否启用
            bk_biz_id: 业务 ID
        """
        request = AlarmStrategySwitch(
            bk_biz_id=bk_biz_id or self.bk_biz_id,
            ids=ids,
            is_enabled=is_enabled,
        )
        return self.switch(request)

    def switch_by_labels(self, request: AlarmStrategySwitchByLabels) -> ApiResponse[Any]:
        """
        根据标签批量启停告警策略

        端点: POST /app/alarm_strategy/switch_by_labels/
        Backend: /api/v4/alarm_strategy_v3/switch_by_labels/

        Args:
            request: 按标签启停请求模型

        Returns:
            包含更新数量的响应
        """
        return self._client.post(f"{self._base_path}/switch_by_labels/", json=request.model_dump())

    def switch_by_labels_action(
        self,
        labels: list[str],
        action: str = "off",
        bk_biz_id: int | None = None,
    ) -> ApiResponse[Any]:
        """
        根据标签批量启停策略（简便方法）

        Args:
            labels: 标签列表
            action: 操作类型，"on" 或 "off"
            bk_biz_id: 业务 ID
        """
        request = AlarmStrategySwitchByLabels(
            bk_biz_id=bk_biz_id or self.bk_biz_id,
            labels=labels,
            action=action,  # type: ignore
        )
        return self.switch_by_labels(request)

    # ==================== Delete 接口 ====================

    def delete(self, request: AlarmStrategyDelete) -> ApiResponse[Any]:
        """
        删除告警策略

        端点: POST /app/alarm_strategy/delete/
        Backend: /api/v4/alarm_strategy_v3/delete/

        Args:
            request: 删除请求模型

        Returns:
            data 为 null 的响应
        """
        return self._client.post(f"{self._base_path}/delete/", json=request.model_dump())

    def delete_v3(self, request: AlarmStrategyDelete) -> ApiResponse[Any]:
        """删除告警策略（V3 迁移版）"""
        return self._client.post(f"{self._base_path}/delete/v3/", json=request.model_dump())

    def delete_by_ids(
        self,
        ids: list[int],
        bk_biz_id: int | None = None,
    ) -> ApiResponse[Any]:
        """
        删除告警策略（简便方法）

        Args:
            ids: 策略 ID 列表
            bk_biz_id: 业务 ID
        """
        request = AlarmStrategyDelete(
            bk_biz_id=bk_biz_id or self.bk_biz_id,
            ids=ids,
        )
        return self.delete(request)

    def delete_by_ids_v3(
        self,
        ids: list[int],
        bk_biz_id: int | None = None,
    ) -> ApiResponse[Any]:
        """删除告警策略（V3，简便方法）"""
        request = AlarmStrategyDelete(
            bk_biz_id=bk_biz_id or self.bk_biz_id,
            ids=ids,
        )
        return self.delete_v3(request)
