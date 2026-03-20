"""
告警策略 CRUD 测试用例

测试流程遵循真实工作流：
1. 创建策略 (Create)
2. 查询验证创建成功 (Read after Create)
3. 修改策略 (Update - 启停/更新)
4. 查询验证修改成功 (Read after Update)
5. 删除策略 (Delete)

测试顺序保证机制：
- 使用类级别状态共享（类属性）
- 测试方法按数字前缀命名（test_01, test_02, ...）
- 使用 conftest.py 中的 strategy_cleaner 统一清理
"""

import time

import pytest

from tests.apigw.clients.alarm_strategy import AlarmStrategyClient
from tests.apigw.models.alarm_strategy import (
    AlarmStrategyDelete,
    AlarmStrategyFactory,
    AlarmStrategySearch,
    AlarmStrategySwitch,
    AlarmStrategySwitchByLabels,
)
from tests.apigw.rules import AlarmStrategyRules
from tests.apigw.utils.assertions import assert_api_success
from tests.apigw.utils.response_validator import assert_response_valid


@pytest.mark.crud
class TestAlarmStrategyCRUD:
    """
    告警策略 CRUD 完整生命周期测试
    """

    # 类级别状态
    strategy_id: int | None = None
    strategy_name: str = ""

    def test_01_create_strategy(
        self,
        alarm_strategy_client: AlarmStrategyClient,
        bk_biz_id: int,
        strategy_cleaner: "StrategyCleaner",
    ) -> None:
        """
        步骤 1: 创建告警策略 (Create)
        """
        TestAlarmStrategyCRUD.strategy_name = f"test_strategy_{int(time.time())}"

        # 使用工厂方法创建策略配置
        request = AlarmStrategyFactory.cpu_usage_strategy(
            bk_biz_id=bk_biz_id,
            name=TestAlarmStrategyCRUD.strategy_name,
            threshold=90,
            is_enabled=False,
            labels=["test", "api_test"],
        )

        response = alarm_strategy_client.save(request)

        assert_api_success(response, "创建策略失败")
        assert_response_valid(
            response,
            AlarmStrategyRules.save_response_with_values(
                expected_name=TestAlarmStrategyCRUD.strategy_name,
                expected_bk_biz_id=bk_biz_id,
                expected_is_enabled=False,
            ),
            message="创建策略响应校验失败",
        )

        TestAlarmStrategyCRUD.strategy_id = response.data["id"]
        strategy_cleaner.register(TestAlarmStrategyCRUD.strategy_id)

    def test_02_search_after_create(
        self,
        alarm_strategy_client: AlarmStrategyClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 2: 查询验证创建成功 (Read after Create)
        """
        assert TestAlarmStrategyCRUD.strategy_id is not None, "前置条件失败：需要先执行 test_01 创建策略"

        # 使用 Model 定义查询参数
        request = AlarmStrategySearch(
            bk_biz_id=bk_biz_id,
            page=1,
            page_size=100,
            conditions=[{"key": "strategy_id", "value": [TestAlarmStrategyCRUD.strategy_id]}],
        )

        response = alarm_strategy_client.search(request)

        assert_api_success(response, "查询策略列表失败")
        assert_response_valid(
            response,
            AlarmStrategyRules.search_response(),
            message="查询策略列表响应校验失败",
        )

        # 验证能查到刚创建的策略
        strategies = response.data.get("strategy_config_list", [])
        found = any(s.get("id") == TestAlarmStrategyCRUD.strategy_id for s in strategies)
        assert found, f"未找到刚创建的策略 ID: {TestAlarmStrategyCRUD.strategy_id}"

        # 验证策略名称
        strategy = next((s for s in strategies if s.get("id") == TestAlarmStrategyCRUD.strategy_id), None)
        assert strategy is not None
        assert strategy.get("name") == TestAlarmStrategyCRUD.strategy_name, "策略名称不匹配"
        assert strategy.get("is_enabled") is False, "策略应该是禁用状态"

    def test_03_switch_enable_strategy(
        self,
        alarm_strategy_client: AlarmStrategyClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 3: 启用告警策略 (Update - Enable)
        """
        assert TestAlarmStrategyCRUD.strategy_id is not None, "前置条件失败：需要先执行 test_01 创建策略"

        # 使用 Model 定义启停参数
        request = AlarmStrategySwitch(
            bk_biz_id=bk_biz_id,
            ids=[TestAlarmStrategyCRUD.strategy_id],
            is_enabled=True,
        )

        response = alarm_strategy_client.switch(request)

        assert_api_success(response, "启用策略失败")
        assert_response_valid(
            response,
            AlarmStrategyRules.switch_response_with_ids([TestAlarmStrategyCRUD.strategy_id]),
            message="启用策略响应校验失败",
        )

    def test_04_search_after_enable(
        self,
        alarm_strategy_client: AlarmStrategyClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 4: 查询验证启用成功 (Read after Enable)
        """
        assert TestAlarmStrategyCRUD.strategy_id is not None, "前置条件失败：需要先执行 test_01 创建策略"

        request = AlarmStrategySearch(
            bk_biz_id=bk_biz_id,
            page=1,
            page_size=100,
            conditions=[{"key": "strategy_id", "value": [TestAlarmStrategyCRUD.strategy_id]}],
        )

        response = alarm_strategy_client.search(request)

        assert_api_success(response, "查询策略失败")

        # 验证策略已启用
        strategies = response.data.get("strategy_config_list", [])
        strategy = next((s for s in strategies if s.get("id") == TestAlarmStrategyCRUD.strategy_id), None)
        assert strategy is not None, f"未找到策略 ID: {TestAlarmStrategyCRUD.strategy_id}"
        assert strategy.get("is_enabled") is True, "策略应该是启用状态"

    def test_05_switch_disable_strategy(
        self,
        alarm_strategy_client: AlarmStrategyClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 5: 停用告警策略 (Update - Disable)
        """
        assert TestAlarmStrategyCRUD.strategy_id is not None, "前置条件失败：需要先执行 test_01 创建策略"

        request = AlarmStrategySwitch(
            bk_biz_id=bk_biz_id,
            ids=[TestAlarmStrategyCRUD.strategy_id],
            is_enabled=False,
        )

        response = alarm_strategy_client.switch(request)

        assert_api_success(response, "停用策略失败")
        assert_response_valid(
            response,
            AlarmStrategyRules.switch_response(),
            message="停用策略响应校验失败",
        )

    def test_06_search_after_disable(
        self,
        alarm_strategy_client: AlarmStrategyClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 6: 查询验证停用成功 (Read after Disable)
        """
        assert TestAlarmStrategyCRUD.strategy_id is not None, "前置条件失败：需要先执行 test_01 创建策略"

        request = AlarmStrategySearch(
            bk_biz_id=bk_biz_id,
            page=1,
            page_size=100,
            conditions=[{"key": "strategy_id", "value": [TestAlarmStrategyCRUD.strategy_id]}],
        )

        response = alarm_strategy_client.search(request)

        assert_api_success(response, "查询策略失败")

        # 验证策略已停用
        strategies = response.data.get("strategy_config_list", [])
        strategy = next((s for s in strategies if s.get("id") == TestAlarmStrategyCRUD.strategy_id), None)
        assert strategy is not None, f"未找到策略 ID: {TestAlarmStrategyCRUD.strategy_id}"
        assert strategy.get("is_enabled") is False, "策略应该是停用状态"

    def test_07_delete_strategy(
        self,
        alarm_strategy_client: AlarmStrategyClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 7: 删除告警策略 (Delete)
        """
        assert TestAlarmStrategyCRUD.strategy_id is not None, "前置条件失败：需要先执行 test_01 创建策略"

        # 使用 Model 定义删除参数
        request = AlarmStrategyDelete(
            bk_biz_id=bk_biz_id,
            ids=[TestAlarmStrategyCRUD.strategy_id],
        )

        response = alarm_strategy_client.delete(request)

        assert_api_success(response, "删除策略失败")
        assert_response_valid(
            response,
            AlarmStrategyRules.delete_response(),
            message="删除策略响应校验失败",
        )

        # 清除状态
        TestAlarmStrategyCRUD.strategy_id = None

    def test_08_search_after_delete(
        self,
        alarm_strategy_client: AlarmStrategyClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 8: 查询验证删除成功 (Read after Delete)
        """
        # 注意：此时 strategy_id 应该是 None（已清除）
        # 我们使用策略名称来验证策略已被删除
        request = AlarmStrategySearch(
            bk_biz_id=bk_biz_id,
            page=1,
            page_size=100,
            conditions=[{"key": "strategy_name", "value": [TestAlarmStrategyCRUD.strategy_name]}],
        )

        response = alarm_strategy_client.search(request)

        assert_api_success(response, "查询策略失败")

        # 验证策略已被删除（查不到）
        strategies = response.data.get("strategy_config_list", [])
        found = any(s.get("name") == TestAlarmStrategyCRUD.strategy_name for s in strategies)
        assert not found, f"策略 {TestAlarmStrategyCRUD.strategy_name} 应该已被删除"


@pytest.mark.crud
class TestAlarmStrategyV3Workflow:
    """
    告警策略 V3 接口完整工作流测试

    测试 V3 版本接口（search_v3, save_v3, delete_v3）的完整 CRUD 流程
    """

    strategy_id: int | None = None
    strategy_name: str = ""

    def test_01_create_v3(
        self,
        alarm_strategy_client: AlarmStrategyClient,
        bk_biz_id: int,
        strategy_cleaner: "StrategyCleaner",
    ) -> None:
        """创建策略（V3）"""
        TestAlarmStrategyV3Workflow.strategy_name = f"test_strategy_v3_{int(time.time())}"

        request = AlarmStrategyFactory.cpu_usage_strategy(
            bk_biz_id=bk_biz_id,
            name=TestAlarmStrategyV3Workflow.strategy_name,
            threshold=85,
            is_enabled=False,
        )

        response = alarm_strategy_client.save_v3(request)

        assert_api_success(response, "创建策略(V3)失败")
        assert_response_valid(
            response,
            AlarmStrategyRules.save_response(),
            message="创建策略(V3)响应校验失败",
        )

        TestAlarmStrategyV3Workflow.strategy_id = response.data["id"]
        strategy_cleaner.register(TestAlarmStrategyV3Workflow.strategy_id)

    def test_02_search_v3_after_create(
        self,
        alarm_strategy_client: AlarmStrategyClient,
        bk_biz_id: int,
    ) -> None:
        """查询验证创建成功（V3）"""
        assert TestAlarmStrategyV3Workflow.strategy_id is not None, "前置条件失败：需要先执行 test_01"

        request = AlarmStrategySearch(
            bk_biz_id=bk_biz_id,
            conditions=[{"key": "strategy_id", "value": [TestAlarmStrategyV3Workflow.strategy_id]}],
        )

        response = alarm_strategy_client.search_v3(request)

        assert_api_success(response, "查询策略(V3)失败")
        assert_response_valid(
            response,
            AlarmStrategyRules.search_response(),
            message="查询策略(V3)响应校验失败",
        )

        # 验证能查到刚创建的策略
        strategies = response.data.get("strategy_config_list", [])
        found = any(s.get("id") == TestAlarmStrategyV3Workflow.strategy_id for s in strategies)
        assert found, f"未找到刚创建的策略 ID: {TestAlarmStrategyV3Workflow.strategy_id}"

    def test_03_delete_v3(
        self,
        alarm_strategy_client: AlarmStrategyClient,
        bk_biz_id: int,
    ) -> None:
        """删除策略（V3）"""
        assert TestAlarmStrategyV3Workflow.strategy_id is not None, "前置条件失败：需要先执行 test_01"

        request = AlarmStrategyDelete(
            bk_biz_id=bk_biz_id,
            ids=[TestAlarmStrategyV3Workflow.strategy_id],
        )

        response = alarm_strategy_client.delete_v3(request)

        assert_api_success(response, "删除策略(V3)失败")
        assert_response_valid(
            response,
            AlarmStrategyRules.delete_response(),
            message="删除策略(V3)响应校验失败",
        )

        TestAlarmStrategyV3Workflow.strategy_id = None


@pytest.mark.crud
class TestAlarmStrategyAdvanced:
    """
    告警策略高级功能测试

    测试以下高级功能：
    - search_without_biz: 跨业务查询
    - switch_by_labels: 按标签批量操作
    """

    def test_01_search_without_biz(
        self,
        alarm_strategy_client: AlarmStrategyClient,
    ) -> None:
        """测试跨业务查询"""
        response = alarm_strategy_client.search_without_biz()

        assert_api_success(response, "查询全业务策略失败")
        assert_response_valid(
            response,
            AlarmStrategyRules.search_without_biz_response(),
            message="查询全业务策略响应校验失败",
        )

    def test_02_switch_by_labels(
        self,
        alarm_strategy_client: AlarmStrategyClient,
        bk_biz_id: int,
    ) -> None:
        """测试按标签批量启停"""
        # 使用 Model 定义请求参数
        request = AlarmStrategySwitchByLabels(
            bk_biz_id=bk_biz_id,
            labels=["test", "api_test"],
            action="off",
        )

        response = alarm_strategy_client.switch_by_labels(request)

        assert_api_success(response, "按标签启停策略失败")
        assert_response_valid(
            response,
            AlarmStrategyRules.switch_by_labels_response(),
            message="按标签启停策略响应校验失败",
        )


# 导入类型提示
if False:  # TYPE_CHECKING workaround for runtime
    from tests.apigw.conftest import StrategyCleaner
