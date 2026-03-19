"""
拨测节点 CRUD 测试用例

测试顺序保证机制：
1. 使用类级别状态共享 (类属性)
2. 测试方法按数字前缀命名 (test_01, test_02, ...)
3. 每个步骤检查前置状态
4. 使用 conftest.py 中的 resource_cleaner 统一清理

测试流程：创建 → 查询 → 修改 → 删除 → 验证删除
"""

import time

import pytest

from tests.apigw.clients.uptime_check import UptimeCheckClient
from tests.apigw.conftest import ResourceCleaner
from tests.apigw.rules import UptimeCheckRules
from tests.apigw.utils.assertions import (
    assert_api_success,
    assert_list_contains_item,
    assert_list_not_contains_item,
)
from tests.apigw.utils.response_validator import (
    assert_data_valid,
    assert_response_valid,
)


@pytest.mark.crud
class TestUptimeCheckNodeCRUD:
    """
    拨测节点 CRUD 完整生命周期测试

    使用类级别状态共享，确保测试按 创建→查询→修改→删除 顺序执行
    """

    # 类级别状态：在测试方法间共享
    node_id: int | None = None
    node_name: str = ""
    original_name: str = ""

    def test_01_create_node(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        node_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """
        步骤 1: 创建拨测节点

        验证：
        - API 调用成功
        - 返回数据包含节点 ID
        - 传入的参数与返回值一致
        """
        TestUptimeCheckNodeCRUD.original_name = node_test_data["name"]
        TestUptimeCheckNodeCRUD.node_name = f"{node_test_data['name']}_{int(time.time())}"

        response = uptime_check_client.node.add(
            bk_biz_id=bk_biz_id,
            name=TestUptimeCheckNodeCRUD.node_name,
            ip=node_test_data["ip"],
            bk_cloud_id=node_test_data.get("bk_cloud_id", 0),
            is_common=node_test_data.get("is_common", False),
            location=node_test_data.get("location", {}),
            carrieroperator=node_test_data.get("carrieroperator", ""),
            ip_type=node_test_data.get("ip_type", 4),
            bk_host_id=node_test_data.get("bk_host_id"),
        )

        # 基础校验
        assert_api_success(response, "创建节点失败")

        # 严格响应校验
        assert_response_valid(
            response,
            UptimeCheckRules.node_response(
                expected_name=TestUptimeCheckNodeCRUD.node_name,
                expected_ip=node_test_data["ip"],
                expected_bk_cloud_id=node_test_data.get("bk_cloud_id", 0),
                expected_bk_biz_id=bk_biz_id,
                expected_ip_type=node_test_data.get("ip_type", 4),
                expected_carrieroperator=node_test_data.get("carrieroperator", ""),
                expected_is_common=node_test_data.get("is_common", False),
                expected_bk_host_id=node_test_data.get("bk_host_id"),
                expected_location=node_test_data.get("location", {}),
            ),
            message="创建节点响应校验失败",
        )

        TestUptimeCheckNodeCRUD.node_id = response.data["id"]
        resource_cleaner.register_node(TestUptimeCheckNodeCRUD.node_id)

    def test_02_query_node_exists(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 2: 查询验证节点存在

        前置条件：test_01_create_node 已执行并成功
        验证：
        - 导出的节点列表中包含刚创建的节点
        - 节点名称匹配
        """
        assert TestUptimeCheckNodeCRUD.node_id is not None, "前置条件失败：需要先执行 test_01_create_node 创建节点"

        response = uptime_check_client.node.list(bk_biz_id=bk_biz_id)
        assert_api_success(response, "查询节点失败")

        # 验证节点存在于列表中
        nodes = response.data if isinstance(response.data, list) else []
        found_node = assert_list_contains_item(
            nodes,
            match_field="id",
            match_value=TestUptimeCheckNodeCRUD.node_id,
            message="创建的节点在列表中未找到: ",
        )

        assert_data_valid(
            found_node,
            UptimeCheckRules.node_list_item(),
            message="节点列表项规则校验失败",
        )
        # 验证节点名称
        assert found_node["name"] == TestUptimeCheckNodeCRUD.node_name, (
            f"节点名称不匹配: 期望 {TestUptimeCheckNodeCRUD.node_name}, 实际 {found_node['name']}"
        )

    def test_03_update_node(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 3: 修改拨测节点

        前置条件：test_01_create_node 已执行并成功
        验证：
        - API 调用成功
        - 节点名称已更新
        """
        assert TestUptimeCheckNodeCRUD.node_id is not None, "前置条件失败：需要先执行 test_01_create_node 创建节点"

        # 修改节点名称
        updated_name = f"{TestUptimeCheckNodeCRUD.node_name}_updated"

        response = uptime_check_client.node.edit(
            bk_biz_id=bk_biz_id,
            id=TestUptimeCheckNodeCRUD.node_id,
            name=updated_name,
        )

        assert_api_success(response, "修改节点失败")

        # 更新类状态
        TestUptimeCheckNodeCRUD.node_name = updated_name

    def test_04_verify_update(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 4: 验证修改生效

        前置条件：test_03_update_node 已执行并成功
        验证：
        - 查询到的节点名称为修改后的名称
        """
        assert TestUptimeCheckNodeCRUD.node_id is not None, "前置条件失败：需要先执行 test_01_create_node 创建节点"

        response = uptime_check_client.node.list(bk_biz_id=bk_biz_id)
        assert_api_success(response, "查询节点失败")

        nodes = response.data if isinstance(response.data, list) else []
        found_node = assert_list_contains_item(
            nodes,
            match_field="id",
            match_value=TestUptimeCheckNodeCRUD.node_id,
            message="修改后的节点在列表中未找到: ",
        )
        assert_data_valid(
            found_node,
            UptimeCheckRules.node_list_item(),
            message="修改后节点列表项规则校验失败",
        )

        # 验证名称已更新
        assert found_node["name"] == TestUptimeCheckNodeCRUD.node_name, (
            f"节点名称未更新: 期望 {TestUptimeCheckNodeCRUD.node_name}, 实际 {found_node['name']}"
        )

    def test_05_delete_node(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 5: 删除拨测节点

        前置条件：test_01_create_node 已执行并成功
        验证：
        - API 调用成功
        """
        assert TestUptimeCheckNodeCRUD.node_id is not None, "前置条件失败：需要先执行 test_01_create_node 创建节点"

        response = uptime_check_client.node.delete(
            bk_biz_id=bk_biz_id,
            id=TestUptimeCheckNodeCRUD.node_id,
        )

        assert_api_success(response, "删除节点失败")

    def test_06_verify_deleted(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 6: 验证节点已删除

        前置条件：test_05_delete_node 已执行并成功
        验证：
        - 导出的节点列表中不包含已删除的节点
        """
        assert TestUptimeCheckNodeCRUD.node_id is not None, "前置条件失败：需要先执行 test_01_create_node 创建节点"

        response = uptime_check_client.node.list(bk_biz_id=bk_biz_id)
        assert_api_success(response, "查询节点失败")

        nodes = response.data if isinstance(response.data, list) else []

        # 验证节点已不在列表中
        assert_list_not_contains_item(
            nodes,
            match_field="id",
            match_value=TestUptimeCheckNodeCRUD.node_id,
            message="节点删除失败，仍存在于列表中: ",
        )

        # 清理类状态
        TestUptimeCheckNodeCRUD.node_id = None


@pytest.mark.crud
class TestUptimeCheckNodeErrorCases:
    """
    拨测节点异常测试用例

    测试各种错误场景的处理
    """

    def test_create_node_missing_required_field(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """测试缺少必填字段时的错误处理"""
        # 缺少 name 字段
        response = uptime_check_client.node.add(
            bk_biz_id=bk_biz_id,
            name="",  # 空名称
            ip="127.0.0.1",
        )

        # 预期返回错误
        assert response.result is False or response.code != 200, "缺少必填字段应返回错误"

    def test_delete_nonexistent_node(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """测试删除不存在的节点（API 为幂等设计，删除不存在的节点也返回成功）"""
        # 使用一个不存在的 ID
        response = uptime_check_client.node.delete(bk_biz_id=bk_biz_id, id=999999999)

        # 幂等设计：删除不存在的节点也返回成功
        assert response.result is True, "删除操作应返回成功（幂等设计）"

    def test_edit_nonexistent_node(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """测试编辑不存在的节点"""
        response = uptime_check_client.node.edit(
            bk_biz_id=bk_biz_id,
            id=999999999,
            name="should_fail",
        )

        # 预期返回错误
        assert response.result is False or response.code != 200, "编辑不存在的节点应返回错误"
