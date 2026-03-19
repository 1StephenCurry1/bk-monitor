"""
拨测模块完整流程测试（E2E）

使用 conftest.py 中的 func_resource_cleaner 统一清理
"""

import time

import pytest

from tests.apigw.clients.uptime_check import UptimeCheckClient
from tests.apigw.conftest import ResourceCleaner
from tests.apigw.rules import UptimeCheckRules
from tests.apigw.utils.assertions import (
    assert_api_success,
    assert_list_contains_item,
)
from tests.apigw.utils.response_validator import (
    assert_data_valid,
    assert_response_valid,
)


@pytest.mark.integration
class TestUptimeCheckFullFlow:
    """
    拨测模块端到端完整流程测试
    """

    def test_complete_uptime_check_flow(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        node_test_data: dict,
        task_test_data: dict,
        group_test_data: dict,
        func_resource_cleaner: ResourceCleaner,
    ) -> None:
        """
        完整的拨测流程测试

        流程：
        1. 创建节点 → 2. 创建分组 → 3. 创建任务 → 4. 查询验证
        → 5. 修改任务 → 6. 验证修改
        """
        timestamp = int(time.time())

        # ==================== 1. 创建节点 ====================
        node_name = f"e2e_node_{timestamp}"
        node_response = uptime_check_client.node.add(
            bk_biz_id=bk_biz_id,
            name=node_name,
            ip=node_test_data["ip"],
            bk_cloud_id=node_test_data.get("bk_cloud_id", 0),
            location=node_test_data.get("location", {}),
            carrieroperator=node_test_data.get("carrieroperator", "内网"),
            ip_type=node_test_data.get("ip_type", 4),
            bk_host_id=node_test_data.get("bk_host_id"),
        )
        assert_api_success(node_response, "步骤1: 创建节点失败")
        # 完整响应校验
        assert_response_valid(
            node_response,
            UptimeCheckRules.node_response(
                expected_name=node_name,
                expected_ip=node_test_data["ip"],
                expected_bk_cloud_id=node_test_data.get("bk_cloud_id", 0),
                expected_bk_biz_id=bk_biz_id,
                expected_ip_type=node_test_data.get("ip_type", 4),
                expected_carrieroperator=node_test_data.get("carrieroperator", "内网"),
                expected_is_common=False,
                expected_bk_host_id=node_test_data.get("bk_host_id"),
                expected_location=node_test_data.get("location"),
            ),
            message="步骤1: 节点响应校验失败",
        )
        node_id = node_response.data["id"]
        func_resource_cleaner.register_node(node_id)

        # ==================== 2. 创建分组 ====================
        group_name = f"e2e_group_{timestamp}"
        group_response = uptime_check_client.group.add(bk_biz_id=bk_biz_id, name=group_name)
        assert_api_success(group_response, "步骤2: 创建分组失败")
        # 完整响应校验
        assert_response_valid(
            group_response,
            UptimeCheckRules.group_response(
                expected_name=group_name,
                expected_bk_biz_id=bk_biz_id,
            ),
            message="步骤2: 分组响应校验失败",
        )
        group_id = group_response.data["id"]
        func_resource_cleaner.register_group(group_id)

        # ==================== 3. 创建任务（关联节点和分组） ====================
        task_name = f"e2e_task_{timestamp}"
        check_interval = task_test_data.get("check_interval", 60)
        task_response = uptime_check_client.task.add(
            bk_biz_id=bk_biz_id,
            name=task_name,
            protocol=task_test_data["protocol"],
            config=task_test_data["config"],
            check_interval=check_interval,
            node_id_list=[node_id],
            groups=[group_id],
            location=task_test_data.get("location", {}),
        )
        assert_api_success(task_response, "步骤3: 创建任务失败")
        # 完整响应校验
        assert_response_valid(
            task_response,
            UptimeCheckRules.task_response(
                expected_name=task_name,
                expected_protocol=task_test_data["protocol"],
                expected_bk_biz_id=bk_biz_id,
            ),
            message="步骤3: 任务响应校验失败",
        )
        task_id = task_response.data["id"]
        func_resource_cleaner.register_task(task_id)

        # ==================== 4. 查询验证 ====================
        node_list_response = uptime_check_client.node.list(bk_biz_id=bk_biz_id)
        assert_api_success(node_list_response, "步骤4: 查询节点失败")
        nodes = node_list_response.data if isinstance(node_list_response.data, list) else []
        found_node = assert_list_contains_item(nodes, "id", node_id, "步骤4: 节点查询验证失败: ")
        assert_data_valid(
            found_node,
            UptimeCheckRules.node_list_item(),
            message="步骤4: 节点列表项规则校验失败",
        )
        assert found_node["name"] == node_name, f"节点名称不匹配: {found_node['name']}"

        # 验证任务
        task_list_response = uptime_check_client.task.list(bk_biz_id=bk_biz_id)
        assert_api_success(task_list_response, "步骤4: 查询任务失败")
        tasks = task_list_response.data if isinstance(task_list_response.data, list) else []
        found_task = assert_list_contains_item(tasks, "id", task_id, "步骤4: 任务查询验证失败: ")
        assert_data_valid(
            found_task,
            UptimeCheckRules.task_list_item(),
            message="步骤4: 任务列表项规则校验失败",
        )
        assert found_task["name"] == task_name, f"任务名称不匹配: {found_task['name']}"

        # ==================== 5. 修改任务 ====================
        updated_task_name = f"{task_name}_updated"
        update_response = uptime_check_client.task.edit(
            bk_biz_id=bk_biz_id,
            id=task_id,
            name=updated_task_name,
            check_interval=120,
        )
        assert_api_success(update_response, "步骤5: 修改任务失败")

        # ==================== 6. 验证修改 ====================
        verify_response = uptime_check_client.task.list(bk_biz_id=bk_biz_id)
        assert_api_success(verify_response, "步骤6: 验证修改失败")
        tasks = verify_response.data if isinstance(verify_response.data, list) else []
        updated_task = assert_list_contains_item(tasks, "id", task_id)
        assert_data_valid(
            updated_task,
            UptimeCheckRules.task_list_item(),
            message="步骤6: 任务列表项规则校验失败",
        )
        assert updated_task["name"] == updated_task_name, (
            f"步骤6: 任务名称未更新: 期望 {updated_task_name}, 实际 {updated_task['name']}"
        )


@pytest.mark.integration
class TestUptimeCheckMultipleResources:
    """
    多资源场景测试

    测试创建多个节点、任务、分组的场景
    """

    def test_multiple_nodes_and_tasks(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        node_test_data: dict,
        task_test_data: dict,
        func_resource_cleaner: ResourceCleaner,
    ) -> None:
        """
        测试创建多个节点和任务

        流程：创建2个节点 → 创建2个任务 → 查询验证
        """
        timestamp = int(time.time())
        node_ids: list[int] = []
        task_ids: list[int] = []

        # ========== 创建2个节点 ==========
        for i in range(2):
            node_name = f"multi_node_{timestamp}_{i}"
            response = uptime_check_client.node.add(
                bk_biz_id=bk_biz_id,
                name=node_name,
                ip=node_test_data["ip"],
                bk_cloud_id=node_test_data.get("bk_cloud_id", 0),
                location=node_test_data.get("location", {}),
                carrieroperator=node_test_data.get("carrieroperator", "移动"),
                ip_type=node_test_data.get("ip_type", 4),
                bk_host_id=node_test_data.get("bk_host_id"),
            )
            assert_api_success(response, f"创建节点 {i} 失败")
            # 完整响应校验
            assert_response_valid(
                response,
                UptimeCheckRules.node_response(
                    expected_name=node_name,
                    expected_ip=node_test_data["ip"],
                    expected_bk_cloud_id=node_test_data.get("bk_cloud_id", 0),
                    expected_bk_biz_id=bk_biz_id,
                    expected_ip_type=node_test_data.get("ip_type", 4),
                    expected_carrieroperator=node_test_data.get("carrieroperator", "移动"),
                    expected_is_common=False,
                    expected_bk_host_id=node_test_data.get("bk_host_id"),
                    expected_location=node_test_data.get("location", {}),
                ),
                message=f"节点 {i} 响应校验失败",
            )
            node_ids.append(response.data["id"])
            func_resource_cleaner.register_node(response.data["id"])

        # ========== 创建2个任务 ==========
        for i in range(2):
            task_name = f"multi_task_{timestamp}_{i}"
            response = uptime_check_client.task.add(
                bk_biz_id=bk_biz_id,
                name=task_name,
                protocol=task_test_data["protocol"],
                config=task_test_data["config"],
                node_id_list=[node_ids[i]],  # 每个任务关联对应的节点
                location=task_test_data.get("location", {}),
            )
            assert_api_success(response, f"创建任务 {i} 失败")
            # 完整响应校验（基于 UptimeCheckTaskSerializer 返回结构，校验所有字段）
            assert_response_valid(
                response,
                UptimeCheckRules.task_response(
                    expected_name=task_name,
                    expected_protocol=task_test_data["protocol"],
                    expected_bk_biz_id=bk_biz_id,
                ),
                message=f"任务 {i} 响应校验失败",
            )
            task_ids.append(response.data["id"])
            func_resource_cleaner.register_task(response.data["id"])

        # ========== 查询验证 ==========
        task_list_response = uptime_check_client.task.list(bk_biz_id=bk_biz_id)
        assert_api_success(task_list_response, "查询任务失败")
        tasks = task_list_response.data if isinstance(task_list_response.data, list) else []

        for task_id in task_ids:
            found_task = assert_list_contains_item(tasks, "id", task_id, f"任务 {task_id} 查询失败: ")
            assert_data_valid(
                found_task,
                UptimeCheckRules.task_list_item(),
                message=f"任务 {task_id} 列表项规则校验失败",
            )
