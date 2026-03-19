"""
拨测任务 CRUD 测试用例

测试顺序保证机制：
1. 使用类级别状态共享 (类属性)
2. 测试方法按数字前缀命名 (test_01, test_02, ...)
3. 任务依赖节点，需先创建节点
4. 使用 conftest.py 中的 resource_cleaner 统一清理

测试流程：创建节点 → 创建任务 → 查询 → 修改 → 验证 → 删除任务 → 删除节点
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
class TestUptimeCheckTaskCRUD:
    """
    拨测任务 CRUD 完整生命周期测试

    注意：任务依赖节点，测试会先创建一个节点，再进行任务 CRUD
    """

    # 类级别状态
    node_id: int | None = None
    task_id: int | None = None
    task_name: str = ""

    def test_01_create_prerequisite_node(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        node_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """
        步骤 1: 创建前置节点

        任务需要关联节点，先创建一个节点
        """
        node_name = f"task_test_node_{int(time.time())}"

        response = uptime_check_client.node.add(
            bk_biz_id=bk_biz_id,
            name=node_name,
            ip=node_test_data["ip"],
            bk_cloud_id=node_test_data.get("bk_cloud_id", 0),
            location=node_test_data.get("location", {}),
            carrieroperator=node_test_data.get("carrieroperator", "内网"),
            ip_type=node_test_data.get("ip_type", 4),
            bk_host_id=node_test_data.get("bk_host_id"),
        )

        assert_api_success(response, "创建前置节点失败")
        TestUptimeCheckTaskCRUD.node_id = response.data["id"]
        resource_cleaner.register_node(TestUptimeCheckTaskCRUD.node_id)

    def test_02_create_task(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        task_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """
        步骤 2: 创建拨测任务

        前置条件：test_01_create_prerequisite_node 已执行
        验证：
        - API 调用成功
        - 必填字段存在（id, create_time, update_time）
        - 传入的参数与返回值一致
        """
        assert TestUptimeCheckTaskCRUD.node_id is not None, "前置条件失败：需要先执行 test_01 创建节点"

        TestUptimeCheckTaskCRUD.task_name = f"test_task_{int(time.time())}"

        response = uptime_check_client.task.add(
            bk_biz_id=bk_biz_id,
            name=TestUptimeCheckTaskCRUD.task_name,
            protocol=task_test_data["protocol"],
            config=task_test_data["config"],
            check_interval=task_test_data.get("check_interval", 60),
            node_id_list=[TestUptimeCheckTaskCRUD.node_id],
            location=task_test_data.get("location", {}),
        )

        # 基础校验
        assert_api_success(response, "创建任务失败")

        # 严格响应校验
        assert_response_valid(
            response,
            UptimeCheckRules.task_response(
                expected_name=TestUptimeCheckTaskCRUD.task_name,
                expected_protocol=task_test_data["protocol"],
                expected_bk_biz_id=bk_biz_id,
            ),
            message="创建任务响应校验失败",
        )

        TestUptimeCheckTaskCRUD.task_id = response.data["id"]
        resource_cleaner.register_task(TestUptimeCheckTaskCRUD.task_id)

    def test_03_query_task_exists(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 3: 查询验证任务存在

        前置条件：test_02_create_task 已执行
        """
        assert TestUptimeCheckTaskCRUD.task_id is not None, "前置条件失败：需要先执行 test_02 创建任务"

        response = uptime_check_client.task.list(bk_biz_id=bk_biz_id)
        assert_api_success(response, "查询任务失败")

        tasks = response.data if isinstance(response.data, list) else []
        found_task = assert_list_contains_item(
            tasks,
            match_field="id",
            match_value=TestUptimeCheckTaskCRUD.task_id,
            message="创建的任务在列表中未找到: ",
        )
        assert_data_valid(
            found_task,
            UptimeCheckRules.task_list_item(),
            message="任务列表项规则校验失败",
        )

        assert found_task["name"] == TestUptimeCheckTaskCRUD.task_name

    def test_04_update_task(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 4: 修改拨测任务
        """
        assert TestUptimeCheckTaskCRUD.task_id is not None, "前置条件失败：需要先执行 test_02 创建任务"

        updated_name = f"{TestUptimeCheckTaskCRUD.task_name}_updated"

        response = uptime_check_client.task.edit(
            bk_biz_id=bk_biz_id,
            id=TestUptimeCheckTaskCRUD.task_id,
            name=updated_name,
            check_interval=120,  # 修改检测间隔
        )

        assert_api_success(response, "修改任务失败")
        TestUptimeCheckTaskCRUD.task_name = updated_name

    def test_05_verify_update(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 5: 验证修改生效
        """
        assert TestUptimeCheckTaskCRUD.task_id is not None, "前置条件失败：需要先执行 test_02 创建任务"

        response = uptime_check_client.task.list(bk_biz_id=bk_biz_id)
        assert_api_success(response, "查询任务失败")

        tasks = response.data if isinstance(response.data, list) else []
        found_task = assert_list_contains_item(
            tasks,
            match_field="id",
            match_value=TestUptimeCheckTaskCRUD.task_id,
        )
        assert_data_valid(
            found_task,
            UptimeCheckRules.task_list_item(),
            message="修改后任务列表项规则校验失败",
        )

        assert found_task["name"] == TestUptimeCheckTaskCRUD.task_name, "任务名称未更新"

    def test_06_delete_task(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 6: 删除拨测任务
        """
        assert TestUptimeCheckTaskCRUD.task_id is not None, "前置条件失败：需要先执行 test_02 创建任务"

        response = uptime_check_client.task.delete(
            bk_biz_id=bk_biz_id,
            id=TestUptimeCheckTaskCRUD.task_id,
        )

        assert_api_success(response, "删除任务失败")

    def test_07_verify_task_deleted(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 7: 验证任务已删除
        """
        assert TestUptimeCheckTaskCRUD.task_id is not None, "前置条件失败：需要先执行 test_02 创建任务"

        response = uptime_check_client.task.list(bk_biz_id=bk_biz_id)
        assert_api_success(response, "查询任务失败")

        tasks = response.data if isinstance(response.data, list) else []
        assert_list_not_contains_item(
            tasks,
            match_field="id",
            match_value=TestUptimeCheckTaskCRUD.task_id,
            message="任务删除失败: ",
        )

        TestUptimeCheckTaskCRUD.task_id = None
