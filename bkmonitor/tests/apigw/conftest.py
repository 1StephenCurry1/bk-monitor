"""
pytest fixtures

提供测试所需的共享 fixtures，包括：
- 配置加载（基于环境）
- API 客户端初始化
- 测试数据管理
- 状态存储（用于 CRUD 顺序保证）
- 自动清理（测试失败时清理残留资源）

使用方式：
    ./run_tests.py --env paas3 -v
    ./run_tests.py --env op -k "test_group"
"""

import logging
from pathlib import Path
from typing import Any
from collections.abc import Generator

import pytest
from dotenv import load_dotenv

# 在导入配置加载器之前，先加载 .env 文件
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

from tests.apigw.clients.uptime_check import UptimeCheckClient
from tests.apigw.utils.config_loader import (
    Settings,
    get_current_environment,
    load_settings,
    load_test_data,
)

logger = logging.getLogger(__name__)


# ============== 配置相关 fixtures ==============


@pytest.fixture(scope="session")
def current_environment() -> str:
    """获取当前测试环境名称"""
    env = get_current_environment()
    logger.info(f"当前测试环境: {env}")
    return env


@pytest.fixture(scope="session")
def settings(current_environment: str) -> Settings:
    """加载全局配置（session 级别，整个测试会话只加载一次）"""
    settings = load_settings(environment=current_environment)
    logger.info(f"已加载 {current_environment} 环境配置")
    logger.info(f"API Base URL: {settings.api_base_url}")
    return settings


@pytest.fixture(scope="session")
def bk_biz_id(settings: Settings) -> int:
    """获取测试业务 ID"""
    return settings.biz.bk_biz_id


# ============== 客户端相关 fixtures ==============


@pytest.fixture(scope="session")
def uptime_check_client(settings: Settings) -> UptimeCheckClient:
    """创建拨测客户端（session 级别，整个测试会话复用）"""
    return UptimeCheckClient(settings)


# ============== 状态存储 fixtures（用于 CRUD 顺序保证） ==============


@pytest.fixture(scope="module")
def state_store() -> dict[str, Any]:
    """
    模块级别状态存储

    用于在同一模块的多个测试函数间传递数据，如：
    - 创建资源后存储 ID
    - 后续测试读取 ID 进行查询/修改/删除

    示例：
        def test_01_create(state_store):
            state_store["node_id"] = created_id

        def test_02_query(state_store):
            node_id = state_store["node_id"]
    """
    return {}


@pytest.fixture(scope="class")
def class_state() -> dict[str, Any]:
    """
    类级别状态存储

    用于在同一测试类的多个测试方法间传递数据
    """
    return {}


# ============== 测试数据 fixtures ==============


@pytest.fixture(scope="session")
def test_data_dir(settings: Settings) -> Path:
    """获取当前环境的测试数据目录路径"""
    return settings.test_data_dir


@pytest.fixture(scope="session")
def uptime_check_test_data(current_environment: str) -> dict[str, Any]:
    """加载当前环境的拨测测试数据"""
    try:
        data = load_test_data("uptime_check.yaml", environment=current_environment)
        logger.info(f"已加载 {current_environment} 环境的拨测测试数据")
        return data
    except FileNotFoundError:
        logger.warning(f"未找到 {current_environment} 环境的拨测测试数据文件")
        return {}


@pytest.fixture(scope="function")
def node_test_data(uptime_check_test_data: dict[str, Any]) -> dict[str, Any]:
    """获取节点测试数据"""
    node_config = uptime_check_test_data["node"]

    return {
        "name": "test_node_auto",
        "bk_host_id": node_config["bk_host_id"],
        "ip": node_config["ip"],
        "bk_cloud_id": node_config["bk_cloud_id"],
        "is_common": False,
        "location": {"country": "中国", "city": "深圳"},
        "carrieroperator": "内网",
        "ip_type": 4,  # IPv4
    }


@pytest.fixture(scope="function")
def task_test_data() -> dict[str, Any]:
    """获取 HTTP 任务测试数据"""
    return {
        "name": "test_task_http_auto",
        "protocol": "HTTP",
        "check_interval": 5,
        "location": {"country": "中国", "city": "深圳"},  # 必填字段
        "config": {
            "method": "GET",
            "url_list": ["https://httpbin.org/get"],
            "headers": [],
            "response_code": "200",
            "response": "",
            "insecure_skip_verify": False,
            "timeout": 5000,
            "period": 60,  # 必填字段：检测周期（秒）
        },
    }


@pytest.fixture(scope="function")
def task_tcp_test_data() -> dict[str, Any]:
    """获取 TCP 任务测试数据（静态 IP 目标，固定参数）"""
    return {
        "name": "test_task_tcp_auto",
        "protocol": "TCP",
        "check_interval": 5,
        "location": {"country": "中国", "city": "深圳"},
        "config": {
            "ip_list": ["220.181.38.150"],  # 百度 IP
            "port": 80,
            "timeout": 5000,
            "period": 60,
        },
    }


@pytest.fixture(scope="function")
def task_tcp_cmdb_test_data(uptime_check_test_data: dict[str, Any]) -> dict[str, Any]:
    """获取 TCP 任务测试数据（CMDB 动态拓扑目标，从配置文件加载）"""
    cmdb_target = uptime_check_test_data["cmdb_target"]["tcp"]

    return {
        "name": "test_task_tcp_cmdb_auto",
        "protocol": "TCP",
        "check_interval": 5,
        "location": {"country": "中国", "city": "深圳"},
        "config": {
            "node_list": cmdb_target["node_list"],
            "port": cmdb_target["port"],
            "timeout": 5000,
            "period": 60,
        },
    }


@pytest.fixture(scope="function")
def task_udp_test_data() -> dict[str, Any]:
    """获取 UDP 任务测试数据（静态 IP 目标，固定参数）"""
    return {
        "name": "test_task_udp_auto",
        "protocol": "UDP",
        "check_interval": 5,
        "location": {"country": "中国", "city": "深圳"},
        "config": {
            "ip_list": ["8.8.8.8"],  # Google DNS
            "port": 53,
            "timeout": 3000,
            "period": 60,
            "request": "",
            "request_format": "raw",
        },
    }


@pytest.fixture(scope="function")
def task_udp_cmdb_test_data(uptime_check_test_data: dict[str, Any]) -> dict[str, Any]:
    """获取 UDP 任务测试数据（CMDB 动态拓扑目标，从配置文件加载）"""
    cmdb_target = uptime_check_test_data["cmdb_target"]["udp"]

    return {
        "name": "test_task_udp_cmdb_auto",
        "protocol": "UDP",
        "check_interval": 5,
        "location": {"country": "中国", "city": "深圳"},
        "config": {
            "node_list": cmdb_target["node_list"],
            "port": cmdb_target["port"],
            "timeout": 3000,
            "period": 60,
            "request": "",
            "request_format": "raw",
        },
    }


@pytest.fixture(scope="function")
def task_icmp_test_data() -> dict[str, Any]:
    """获取 ICMP 任务测试数据（静态 IP 目标，固定参数）"""
    return {
        "name": "test_task_icmp_auto",
        "protocol": "ICMP",
        "check_interval": 5,
        "location": {"country": "中国", "city": "深圳"},
        "config": {
            "ip_list": ["8.8.8.8"],  # Google DNS
            "timeout": 5000,
            "max_rtt": 3000,
            "total_num": 3,
            "period": 60,
        },
    }


@pytest.fixture(scope="function")
def task_icmp_cmdb_test_data(uptime_check_test_data: dict[str, Any]) -> dict[str, Any]:
    """获取 ICMP 任务测试数据（CMDB 动态拓扑目标，从配置文件加载）"""
    cmdb_target = uptime_check_test_data["cmdb_target"]["icmp"]

    return {
        "name": "test_task_icmp_cmdb_auto",
        "protocol": "ICMP",
        "check_interval": 5,
        "location": {"country": "中国", "city": "深圳"},
        "config": {
            "node_list": cmdb_target["node_list"],
            "timeout": 5000,
            "max_rtt": 3000,
            "total_num": 3,
            "period": 60,
        },
    }


@pytest.fixture(scope="function")
def group_test_data() -> dict[str, Any]:
    """获取分组测试数据（固定参数，无需配置化）"""
    return {
        "name": "test_group_auto",
        "logo": "",
    }


# ============== 自动清理 fixtures ==============


class ResourceCleaner:
    """资源清理器，统一管理测试资源的注册与清理"""

    def __init__(self, client: UptimeCheckClient, bk_biz_id: int) -> None:
        self.client = client
        self.bk_biz_id = bk_biz_id
        self._tasks: list[int] = []
        self._groups: list[int] = []
        self._nodes: list[int] = []

    def register_task(self, task_id: int) -> None:
        """注册待清理的任务"""
        self._tasks.append(task_id)

    def register_group(self, group_id: int) -> None:
        """注册待清理的分组"""
        self._groups.append(group_id)

    def register_node(self, node_id: int) -> None:
        """注册待清理的节点"""
        self._nodes.append(node_id)

    def cleanup(self) -> None:
        """执行清理：任务 → 分组 → 节点（依赖顺序）"""
        # 1. 清理任务
        for task_id in self._tasks:
            try:
                self.client.task.delete(bk_biz_id=self.bk_biz_id, id=task_id)
                logger.info(f"已清理任务: {task_id}")
            except Exception as e:
                logger.warning(f"清理任务 {task_id} 失败: {e}")

        # 2. 清理分组
        for group_id in self._groups:
            try:
                self.client.group.delete(bk_biz_id=self.bk_biz_id, id=group_id)
                logger.info(f"已清理分组: {group_id}")
            except Exception as e:
                logger.warning(f"清理分组 {group_id} 失败: {e}")

        # 3. 清理节点
        for node_id in self._nodes:
            try:
                self.client.node.delete(bk_biz_id=self.bk_biz_id, id=node_id)
                logger.info(f"已清理节点: {node_id}")
            except Exception as e:
                logger.warning(f"清理节点 {node_id} 失败: {e}")


@pytest.fixture(scope="module")
def resource_cleaner(
    uptime_check_client: UptimeCheckClient,
    bk_biz_id: int,
) -> Generator[ResourceCleaner, None, None]:
    """
    模块级别资源清理器
    """
    cleaner = ResourceCleaner(uptime_check_client, bk_biz_id)
    yield cleaner
    logger.info("开始清理测试资源...")
    cleaner.cleanup()
    logger.info("资源清理完成")


@pytest.fixture(scope="function")
def func_resource_cleaner(
    uptime_check_client: UptimeCheckClient,
    bk_biz_id: int,
) -> Generator[ResourceCleaner, None, None]:
    """
    函数级别资源清理器

    用于单个测试函数内的资源清理
    """
    cleaner = ResourceCleaner(uptime_check_client, bk_biz_id)
    yield cleaner
    cleaner.cleanup()


# ============== pytest 配置 ==============


def pytest_configure(config: pytest.Config) -> None:
    """pytest 配置钩子"""
    # 注册自定义标记
    config.addinivalue_line("markers", "slow: 标记为慢速测试")
    config.addinivalue_line("markers", "integration: 标记为集成测试")
    config.addinivalue_line("markers", "crud: 标记为 CRUD 测试")


def pytest_collection_modifyitems(
    session: pytest.Session,
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """
    pytest 收集测试项后的钩子

    确保同一个类中的测试按定义顺序执行（基于方法名排序）
    同时保证不同类之间的测试不会交叉执行
    """

    # 按 (模块路径, 类名, 方法名) 排序，确保：
    # 1. 同一模块的测试在一起
    # 2. 同一类的测试在一起
    # 3. 同一类内按方法名排序 (test_01 < test_02 < test_03)
    def sort_key(item: pytest.Item) -> tuple[str, str, str]:
        # 获取模块路径
        module_path = str(item.fspath) if hasattr(item, "fspath") else ""
        # 获取类名（如果有的话）
        class_name = item.cls.__name__ if item.cls else ""
        # 获取方法名
        method_name = item.name
        return (module_path, class_name, method_name)

    items.sort(key=sort_key)
