"""
拨测分组 CRUD 测试用例

测试顺序保证机制：
1. 使用类级别状态共享 (类属性)
2. 测试方法按数字前缀命名 (test_01, test_02, ...)
3. 使用 conftest.py 中的 resource_cleaner 统一清理

测试流程：创建分组 → 查询 → 修改 → 删除 → 验证删除
"""

import time

import pytest

from tests.apigw.clients.uptime_check import UptimeCheckClient
from tests.apigw.conftest import ResourceCleaner
from tests.apigw.rules import UptimeCheckRules
from tests.apigw.utils.assertions import assert_api_success
from tests.apigw.utils.response_validator import assert_data_valid, assert_response_valid


@pytest.mark.crud
class TestUptimeCheckGroupCRUD:
    """
    拨测分组 CRUD 完整生命周期测试
    """

    # 类级别状态
    group_id: int | None = None
    group_name: str = ""

    def test_01_create_group(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        group_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """
        步骤 1: 创建拨测分组
        """
        TestUptimeCheckGroupCRUD.group_name = f"test_group_{int(time.time())}"

        response = uptime_check_client.group.add(
            bk_biz_id=bk_biz_id,
            name=TestUptimeCheckGroupCRUD.group_name,
            logo=group_test_data.get("logo", ""),
        )

        assert_api_success(response, "创建分组失败")
        assert_response_valid(
            response,
            UptimeCheckRules.group_response(
                expected_name=TestUptimeCheckGroupCRUD.group_name,
                expected_bk_biz_id=bk_biz_id,
            ),
            message="创建分组响应校验失败",
        )

        TestUptimeCheckGroupCRUD.group_id = response.data["id"]
        resource_cleaner.register_group(TestUptimeCheckGroupCRUD.group_id)

    def test_02_query_group(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 2: 查询拨测分组列表，验证新创建的分组存在
        """
        assert TestUptimeCheckGroupCRUD.group_id is not None, "前置条件失败：需要先执行 test_01 创建分组"

        response = uptime_check_client.group.list(bk_biz_id=bk_biz_id)
        assert_api_success(response, "查询分组列表失败")

        # 从列表中查找创建的分组
        groups = response.data if isinstance(response.data, list) else []
        found_group = next(
            (g for g in groups if g.get("id") == TestUptimeCheckGroupCRUD.group_id),
            None,
        )
        assert found_group is not None, f"查询验证失败: 未找到 id={TestUptimeCheckGroupCRUD.group_id} 的分组"

        assert_data_valid(
            found_group,
            UptimeCheckRules.group_list_item(),
            message="分组列表项规则校验失败",
        )

    def test_03_update_group(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 3: 修改拨测分组
        """
        assert TestUptimeCheckGroupCRUD.group_id is not None, "前置条件失败：需要先执行 test_01 创建分组"

        updated_name = f"{TestUptimeCheckGroupCRUD.group_name}_updated"

        response = uptime_check_client.group.edit(
            bk_biz_id=bk_biz_id,
            id=TestUptimeCheckGroupCRUD.group_id,
            name=updated_name,
        )

        assert_api_success(response, "修改分组失败")
        assert_response_valid(
            response,
            UptimeCheckRules.group_response(
                expected_name=updated_name,
                expected_bk_biz_id=bk_biz_id,
            ),
            message="修改分组响应校验失败",
        )
        TestUptimeCheckGroupCRUD.group_name = updated_name

    def test_04_delete_group(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """
        步骤 4: 删除拨测分组
        """
        assert TestUptimeCheckGroupCRUD.group_id is not None, "前置条件失败：需要先执行 test_01 创建分组"

        response = uptime_check_client.group.delete(
            bk_biz_id=bk_biz_id,
            id=TestUptimeCheckGroupCRUD.group_id,
        )

        assert_api_success(response, "删除分组失败")
        assert_response_valid(
            response,
            UptimeCheckRules.group_delete_response(),
            message="删除分组响应校验失败",
        )
        TestUptimeCheckGroupCRUD.group_id = None
