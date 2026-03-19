"""
多协议拨测任务测试用例

覆盖场景：
- HTTP 协议（GET/POST/PUT/DELETE 方法）
- TCP 协议
- UDP 协议
- ICMP 协议

测试流程：创建节点 → 创建任务 → 查询验证 → 删除任务 → 删除节点
使用 conftest.py 中的 resource_cleaner 统一清理
"""

import time
from typing import Any

import pytest

from tests.apigw.clients.uptime_check import UptimeCheckClient
from tests.apigw.conftest import ResourceCleaner
from tests.apigw.rules import UptimeCheckRules
from tests.apigw.utils.assertions import (
    assert_api_success,
    assert_list_contains_item,
)
from tests.apigw.utils.response_validator import assert_data_valid


# ============== HTTP 协议测试 ==============


@pytest.mark.crud
class TestHTTPProtocolMethods:
    """
    HTTP 协议多方法测试

    测试 HTTP 拨测任务支持的各种请求方法：GET, POST, PUT, DELETE
    """

    node_id: int | None = None

    def test_01_create_node(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        node_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """创建前置节点"""
        response = uptime_check_client.node.add(
            bk_biz_id=bk_biz_id,
            name=f"http_method_test_node_{int(time.time())}",
            ip=node_test_data["ip"],
            bk_cloud_id=node_test_data.get("bk_cloud_id", 0),
            location=node_test_data.get("location", {}),
            carrieroperator=node_test_data.get("carrieroperator", "内网"),
            ip_type=node_test_data.get("ip_type", 4),
            bk_host_id=node_test_data.get("bk_host_id"),
        )
        assert_api_success(response, "创建节点失败")
        TestHTTPProtocolMethods.node_id = response.data["id"]
        resource_cleaner.register_node(TestHTTPProtocolMethods.node_id)

    def test_02_http_get_method(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        task_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """测试 HTTP GET 方法"""
        assert TestHTTPProtocolMethods.node_id is not None

        task_id = self._create_and_verify_http_task(
            uptime_check_client,
            bk_biz_id,
            method="GET",
            url="https://httpbin.org/get",
            task_name=f"http_get_task_{int(time.time())}",
            location=task_test_data.get("location", {}),
        )
        resource_cleaner.register_task(task_id)

    def test_03_http_post_method(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        task_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """测试 HTTP POST 方法"""
        assert TestHTTPProtocolMethods.node_id is not None

        task_id = self._create_and_verify_http_task(
            uptime_check_client,
            bk_biz_id,
            method="POST",
            url="https://httpbin.org/post",
            task_name=f"http_post_task_{int(time.time())}",
            body={
                "data_type": "raw",
                "content": '{"test": "data"}',
                "content_type": "json",
            },
            location=task_test_data.get("location", {}),
        )
        resource_cleaner.register_task(task_id)

    def test_04_http_put_method(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        task_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """测试 HTTP PUT 方法"""
        assert TestHTTPProtocolMethods.node_id is not None

        task_id = self._create_and_verify_http_task(
            uptime_check_client,
            bk_biz_id,
            method="PUT",
            url="https://httpbin.org/put",
            task_name=f"http_put_task_{int(time.time())}",
            body={
                "data_type": "raw",
                "content": '{"update": "data"}',
                "content_type": "json",
            },
            location=task_test_data.get("location", {}),
        )
        resource_cleaner.register_task(task_id)

    def test_05_http_delete_method(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        task_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """测试 HTTP DELETE 方法"""
        assert TestHTTPProtocolMethods.node_id is not None

        task_id = self._create_and_verify_http_task(
            uptime_check_client,
            bk_biz_id,
            method="DELETE",
            url="https://httpbin.org/delete",
            task_name=f"http_delete_task_{int(time.time())}",
            location=task_test_data.get("location", {}),
        )
        resource_cleaner.register_task(task_id)

    def test_06_http_with_custom_headers(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        task_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """测试 HTTP 自定义请求头"""
        assert TestHTTPProtocolMethods.node_id is not None

        task_id = self._create_and_verify_http_task(
            uptime_check_client,
            bk_biz_id,
            method="GET",
            url="https://httpbin.org/headers",
            task_name=f"http_headers_task_{int(time.time())}",
            headers=[
                {"header_name": "X-Custom-Header", "header_value": "test-value"},
                {"header_name": "Authorization", "header_value": "Bearer test_token"},
            ],
            location=task_test_data.get("location", {}),
        )
        resource_cleaner.register_task(task_id)

    def test_07_http_response_validation(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        task_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """测试 HTTP 响应码验证"""
        assert TestHTTPProtocolMethods.node_id is not None

        # 测试 200 响应
        task_id = self._create_and_verify_http_task(
            uptime_check_client,
            bk_biz_id,
            method="GET",
            url="https://httpbin.org/status/200",
            task_name=f"http_status_200_task_{int(time.time())}",
            response_code="200",
            location=task_test_data.get("location", {}),
        )
        resource_cleaner.register_task(task_id)

        # 测试 201 响应
        task_id = self._create_and_verify_http_task(
            uptime_check_client,
            bk_biz_id,
            method="GET",
            url="https://httpbin.org/status/201",
            task_name=f"http_status_201_task_{int(time.time())}",
            response_code="201",
            location=task_test_data.get("location", {}),
        )
        resource_cleaner.register_task(task_id)

    def _create_and_verify_http_task(
        self,
        client: UptimeCheckClient,
        bk_biz_id: int,
        method: str,
        url: str,
        task_name: str,
        headers: list[dict[str, str]] | None = None,
        body: dict[str, Any] | None = None,
        response_code: str = "200",
        location: dict[str, Any] | None = None,
    ) -> int:
        """创建并验证 HTTP 任务"""
        assert TestHTTPProtocolMethods.node_id is not None, "节点 ID 不能为空"

        config: dict[str, Any] = {
            "method": method,
            "url_list": [url],
            "headers": headers or [],
            "response_code": response_code,
            "response_format": "eq",
            "insecure_skip_verify": False,
            "timeout": 5000,
            "period": 60,
        }

        if body:
            config["body"] = body

        response = client.task.add(
            bk_biz_id=bk_biz_id,
            name=task_name,
            protocol="HTTP",
            config=config,
            check_interval=60,
            node_id_list=[TestHTTPProtocolMethods.node_id],
            location=location or {},
        )

        assert_api_success(response, f"创建 HTTP {method} 任务失败")
        task_id = response.data["id"]

        # 验证任务存在
        list_response = client.task.list(bk_biz_id=bk_biz_id)
        assert_api_success(list_response, "查询任务失败")
        tasks = list_response.data if isinstance(list_response.data, list) else []
        found_task = assert_list_contains_item(tasks, "id", task_id, f"HTTP {method} 任务未找到: ")
        assert_data_valid(
            found_task,
            UptimeCheckRules.task_list_item(),
            message=f"HTTP {method} 任务列表项规则校验失败",
        )

        return task_id


# ============== TCP 协议测试（静态 IP + CMDB 动态拓扑） ==============


@pytest.mark.crud
class TestTCPProtocol:
    """
    TCP 协议测试

    同时测试两种目标类型：
    1. 静态 IP 目标 - 直接指定 IP 地址
    2. CMDB 动态拓扑目标 - 通过 CMDB 拓扑选择目标主机
    """

    node_id: int | None = None
    static_ip_task_id: int | None = None
    cmdb_task_id: int | None = None

    def test_01_create_node(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        node_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """创建前置节点"""
        response = uptime_check_client.node.add(
            bk_biz_id=bk_biz_id,
            name=f"tcp_test_node_{int(time.time())}",
            ip=node_test_data["ip"],
            bk_cloud_id=node_test_data.get("bk_cloud_id", 0),
            location=node_test_data.get("location", {}),
            carrieroperator=node_test_data.get("carrieroperator", "内网"),
            ip_type=node_test_data.get("ip_type", 4),
            bk_host_id=node_test_data.get("bk_host_id"),
        )
        assert_api_success(response, "创建节点失败")
        TestTCPProtocol.node_id = response.data["id"]
        resource_cleaner.register_node(TestTCPProtocol.node_id)

    def test_02_create_tcp_task_static_ip(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        task_tcp_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """创建 TCP 任务（静态 IP 目标）"""
        assert TestTCPProtocol.node_id is not None

        response = uptime_check_client.task.add(
            bk_biz_id=bk_biz_id,
            name=f"tcp_static_ip_task_{int(time.time())}",
            protocol="TCP",
            config=task_tcp_test_data["config"],
            check_interval=task_tcp_test_data.get("check_interval", 60),
            node_id_list=[TestTCPProtocol.node_id],
            location=task_tcp_test_data.get("location", {}),
        )

        assert_api_success(response, "创建 TCP 静态 IP 任务失败")
        TestTCPProtocol.static_ip_task_id = response.data["id"]
        resource_cleaner.register_task(TestTCPProtocol.static_ip_task_id)

    def test_03_create_tcp_task_cmdb(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        task_tcp_cmdb_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """创建 TCP 任务（CMDB 动态拓扑目标）"""
        assert TestTCPProtocol.node_id is not None

        response = uptime_check_client.task.add(
            bk_biz_id=bk_biz_id,
            name=f"tcp_cmdb_task_{int(time.time())}",
            protocol="TCP",
            config=task_tcp_cmdb_test_data["config"],
            check_interval=task_tcp_cmdb_test_data.get("check_interval", 60),
            node_id_list=[TestTCPProtocol.node_id],
            location=task_tcp_cmdb_test_data.get("location", {}),
        )

        assert_api_success(response, "创建 TCP CMDB 目标任务失败")
        TestTCPProtocol.cmdb_task_id = response.data["id"]
        resource_cleaner.register_task(TestTCPProtocol.cmdb_task_id)

    def test_04_verify_tcp_tasks(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """验证两种 TCP 任务都创建成功"""
        assert TestTCPProtocol.static_ip_task_id is not None
        assert TestTCPProtocol.cmdb_task_id is not None

        response = uptime_check_client.task.list(bk_biz_id=bk_biz_id)
        assert_api_success(response, "查询任务失败")

        tasks = response.data if isinstance(response.data, list) else []

        # 验证静态 IP 任务
        static_task = assert_list_contains_item(
            tasks, "id", TestTCPProtocol.static_ip_task_id, "TCP 静态 IP 任务未找到: "
        )
        assert_data_valid(
            static_task,
            UptimeCheckRules.task_list_item(),
            message="TCP 静态 IP 任务列表项规则校验失败",
        )

        # 验证 CMDB 任务
        cmdb_task = assert_list_contains_item(tasks, "id", TestTCPProtocol.cmdb_task_id, "TCP CMDB 任务未找到: ")
        assert_data_valid(
            cmdb_task,
            UptimeCheckRules.task_list_item(),
            message="TCP CMDB 任务列表项规则校验失败",
        )


# ============== UDP 协议测试（静态 IP + CMDB 动态拓扑） ==============


@pytest.mark.crud
class TestUDPProtocol:
    """
    UDP 协议测试

    同时测试两种目标类型：
    1. 静态 IP 目标 - 直接指定 IP 地址（如 DNS 服务器）
    2. CMDB 动态拓扑目标 - 通过 CMDB 拓扑选择目标主机
    """

    node_id: int | None = None
    static_ip_task_id: int | None = None
    cmdb_task_id: int | None = None

    def test_01_create_node(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        node_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """创建前置节点"""
        response = uptime_check_client.node.add(
            bk_biz_id=bk_biz_id,
            name=f"udp_test_node_{int(time.time())}",
            ip=node_test_data["ip"],
            bk_cloud_id=node_test_data.get("bk_cloud_id", 0),
            location=node_test_data.get("location", {}),
            carrieroperator=node_test_data.get("carrieroperator", "内网"),
            ip_type=node_test_data.get("ip_type", 4),
            bk_host_id=node_test_data.get("bk_host_id"),
        )
        assert_api_success(response, "创建节点失败")
        TestUDPProtocol.node_id = response.data["id"]
        resource_cleaner.register_node(TestUDPProtocol.node_id)

    def test_02_create_udp_task_static_ip(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        task_udp_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """创建 UDP 任务（静态 IP 目标）"""
        assert TestUDPProtocol.node_id is not None

        response = uptime_check_client.task.add(
            bk_biz_id=bk_biz_id,
            name=f"udp_static_ip_task_{int(time.time())}",
            protocol="UDP",
            config=task_udp_test_data["config"],
            check_interval=task_udp_test_data.get("check_interval", 60),
            node_id_list=[TestUDPProtocol.node_id],
            location=task_udp_test_data.get("location", {}),
        )

        assert_api_success(response, "创建 UDP 静态 IP 任务失败")
        TestUDPProtocol.static_ip_task_id = response.data["id"]
        resource_cleaner.register_task(TestUDPProtocol.static_ip_task_id)

    def test_03_create_udp_task_cmdb(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        task_udp_cmdb_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """创建 UDP 任务（CMDB 动态拓扑目标）"""
        assert TestUDPProtocol.node_id is not None

        response = uptime_check_client.task.add(
            bk_biz_id=bk_biz_id,
            name=f"udp_cmdb_task_{int(time.time())}",
            protocol="UDP",
            config=task_udp_cmdb_test_data["config"],
            check_interval=task_udp_cmdb_test_data.get("check_interval", 60),
            node_id_list=[TestUDPProtocol.node_id],
            location=task_udp_cmdb_test_data.get("location", {}),
        )

        assert_api_success(response, "创建 UDP CMDB 目标任务失败")
        TestUDPProtocol.cmdb_task_id = response.data["id"]
        resource_cleaner.register_task(TestUDPProtocol.cmdb_task_id)

    def test_04_verify_udp_tasks(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """验证两种 UDP 任务都创建成功"""
        assert TestUDPProtocol.static_ip_task_id is not None
        assert TestUDPProtocol.cmdb_task_id is not None

        response = uptime_check_client.task.list(bk_biz_id=bk_biz_id)
        assert_api_success(response, "查询任务失败")

        tasks = response.data if isinstance(response.data, list) else []

        # 验证静态 IP 任务
        static_task = assert_list_contains_item(
            tasks, "id", TestUDPProtocol.static_ip_task_id, "UDP 静态 IP 任务未找到: "
        )
        assert_data_valid(
            static_task,
            UptimeCheckRules.task_list_item(),
            message="UDP 静态 IP 任务列表项规则校验失败",
        )

        # 验证 CMDB 任务
        cmdb_task = assert_list_contains_item(tasks, "id", TestUDPProtocol.cmdb_task_id, "UDP CMDB 任务未找到: ")
        assert_data_valid(
            cmdb_task,
            UptimeCheckRules.task_list_item(),
            message="UDP CMDB 任务列表项规则校验失败",
        )


# ============== ICMP 协议测试（静态 IP + CMDB 动态拓扑） ==============


@pytest.mark.crud
class TestICMPProtocol:
    """
    ICMP 协议测试

    同时测试两种目标类型：
    1. 静态 IP 目标 - 直接指定 IP 地址
    2. CMDB 动态拓扑目标 - 通过 CMDB 拓扑或 bk_host_id 选择目标主机
    """

    node_id: int | None = None
    static_ip_task_id: int | None = None
    cmdb_task_id: int | None = None

    def test_01_create_node(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        node_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """创建前置节点"""
        response = uptime_check_client.node.add(
            bk_biz_id=bk_biz_id,
            name=f"icmp_test_node_{int(time.time())}",
            ip=node_test_data["ip"],
            bk_cloud_id=node_test_data.get("bk_cloud_id", 0),
            location=node_test_data.get("location", {}),
            carrieroperator=node_test_data.get("carrieroperator", "内网"),
            ip_type=node_test_data.get("ip_type", 4),
            bk_host_id=node_test_data.get("bk_host_id"),
        )
        assert_api_success(response, "创建节点失败")
        TestICMPProtocol.node_id = response.data["id"]
        resource_cleaner.register_node(TestICMPProtocol.node_id)

    def test_02_create_icmp_task_static_ip(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        task_icmp_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """创建 ICMP 任务（静态 IP 目标）"""
        assert TestICMPProtocol.node_id is not None

        response = uptime_check_client.task.add(
            bk_biz_id=bk_biz_id,
            name=f"icmp_static_ip_task_{int(time.time())}",
            protocol="ICMP",
            config=task_icmp_test_data["config"],
            check_interval=task_icmp_test_data.get("check_interval", 60),
            node_id_list=[TestICMPProtocol.node_id],
            location=task_icmp_test_data.get("location", {}),
        )

        assert_api_success(response, "创建 ICMP 静态 IP 任务失败")
        TestICMPProtocol.static_ip_task_id = response.data["id"]
        resource_cleaner.register_task(TestICMPProtocol.static_ip_task_id)

    def test_03_create_icmp_task_cmdb(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
        task_icmp_cmdb_test_data: dict,
        resource_cleaner: ResourceCleaner,
    ) -> None:
        """创建 ICMP 任务（CMDB 动态拓扑目标）"""
        assert TestICMPProtocol.node_id is not None

        response = uptime_check_client.task.add(
            bk_biz_id=bk_biz_id,
            name=f"icmp_cmdb_task_{int(time.time())}",
            protocol="ICMP",
            config=task_icmp_cmdb_test_data["config"],
            check_interval=task_icmp_cmdb_test_data.get("check_interval", 60),
            node_id_list=[TestICMPProtocol.node_id],
            location=task_icmp_cmdb_test_data.get("location", {}),
        )

        assert_api_success(response, "创建 ICMP CMDB 目标任务失败")
        TestICMPProtocol.cmdb_task_id = response.data["id"]
        resource_cleaner.register_task(TestICMPProtocol.cmdb_task_id)

    def test_04_verify_icmp_tasks(
        self,
        uptime_check_client: UptimeCheckClient,
        bk_biz_id: int,
    ) -> None:
        """验证两种 ICMP 任务都创建成功"""
        assert TestICMPProtocol.static_ip_task_id is not None
        assert TestICMPProtocol.cmdb_task_id is not None

        response = uptime_check_client.task.list(bk_biz_id=bk_biz_id)
        assert_api_success(response, "查询任务失败")

        tasks = response.data if isinstance(response.data, list) else []

        # 验证静态 IP 任务
        static_task = assert_list_contains_item(
            tasks, "id", TestICMPProtocol.static_ip_task_id, "ICMP 静态 IP 任务未找到: "
        )
        assert_data_valid(
            static_task,
            UptimeCheckRules.task_list_item(),
            message="ICMP 静态 IP 任务列表项规则校验失败",
        )

        # 验证 CMDB 任务
        cmdb_task = assert_list_contains_item(tasks, "id", TestICMPProtocol.cmdb_task_id, "ICMP CMDB 任务未找到: ")
        assert_data_valid(
            cmdb_task,
            UptimeCheckRules.task_list_item(),
            message="ICMP CMDB 任务列表项规则校验失败",
        )
