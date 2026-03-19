"""
拨测 API 客户端

提供拨测节点、任务、分组的 CRUD 操作
"""

from __future__ import annotations

from typing import Any

from tests.apigw.clients.base import BaseApiClient
from tests.apigw.models.base import ApiResponse
from tests.apigw.models.uptime_check import (
    HttpTaskConfig,
    IcmpTaskConfig,
    TcpUdpTaskConfig,
    UptimeCheckGroupAddTask,
    UptimeCheckGroupCreate,
    UptimeCheckGroupDelete,
    UptimeCheckGroupRemoveTask,
    UptimeCheckGroupUpdate,
    UptimeCheckNodeCreate,
    UptimeCheckNodeDelete,
    UptimeCheckNodeUpdate,
    UptimeCheckTaskChangeStatus,
    UptimeCheckTaskDelete,
    UptimeCheckTaskDeploy,
)
from tests.apigw.utils.config_loader import Settings


class UptimeCheckNodeClient:
    """拨测节点 API 客户端"""

    def __init__(self, api_client: BaseApiClient) -> None:
        self._client = api_client
        self._base_path = "uptime_check/node"

    def list(self, bk_biz_id: int) -> ApiResponse[Any]:
        """
        获取拨测节点列表

        Args:
            bk_biz_id: 业务 ID

        Returns:
            包含节点列表的响应，每个节点包含 id, name, ip 等字段
        """
        return self._client.get(f"{self._base_path}/list/", params={"bk_biz_id": bk_biz_id})

    def add(
        self,
        bk_biz_id: int,
        name: str,
        ip: str,
        bk_cloud_id: int = 0,
        is_common: bool = False,
        location: dict[str, Any] | None = None,
        carrieroperator: str = "内网",
        ip_type: int = 4,
        bk_host_id: int | None = None,
        **kwargs: Any,
    ) -> ApiResponse[Any]:
        """
        新增拨测节点

        Args:
            bk_biz_id: 业务 ID
            name: 节点名称
            ip: 节点 IP
            bk_cloud_id: 云区域 ID
            is_common: 是否为公共节点
            location: 地理位置
            carrieroperator: 运营商（内网/联通/移动/电信/其他）
            ip_type: IP 类型（0=ALL, 4=IPv4, 6=IPv6）
            bk_host_id: 主机 ID
        """
        data = UptimeCheckNodeCreate(
            bk_biz_id=bk_biz_id,
            name=name,
            ip=ip,
            bk_cloud_id=bk_cloud_id,
            plat_id=bk_cloud_id,  # 兼容旧字段名
            is_common=is_common,
            location=location or {},
            carrieroperator=carrieroperator,
            ip_type=ip_type,
            bk_host_id=bk_host_id,
            **kwargs,
        )
        return self._client.post(f"{self._base_path}/create/", json=data.model_dump(exclude_none=True))

    def edit(
        self,
        bk_biz_id: int,
        id: int,
        name: str | None = None,
        is_common: bool | None = None,
        location: dict[str, Any] | None = None,
        carrieroperator: str | None = None,
    ) -> ApiResponse[Any]:
        """
        编辑拨测节点

        Args:
            bk_biz_id: 业务 ID
            id: 节点 ID
            name: 节点名称
            is_common: 是否为公共节点
            location: 地理位置
            carrieroperator: 运营商
        """
        data = UptimeCheckNodeUpdate(
            bk_biz_id=bk_biz_id,
            id=id,
            name=name,
            is_common=is_common,
            location=location,
            carrieroperator=carrieroperator,
        )
        return self._client.post(f"{self._base_path}/edit/", json=data.model_dump(exclude_none=True, by_alias=True))

    def delete(self, bk_biz_id: int, id: int) -> ApiResponse[Any]:
        """
        删除拨测节点

        Args:
            bk_biz_id: 业务 ID
            id: 节点 ID
        """
        data = UptimeCheckNodeDelete(bk_biz_id=bk_biz_id, id=id)
        return self._client.post(f"{self._base_path}/delete/", json=data.model_dump(by_alias=True))


class UptimeCheckNodeCollectorClient:
    """拨测节点导入导出客户端"""

    def __init__(self, api_client: BaseApiClient) -> None:
        self._client = api_client
        self._base_path = "uptime_check/node"

    def import_nodes(self, bk_biz_id: int, conf_list: list[dict[str, Any]]) -> ApiResponse[Any]:
        """
        导入拨测节点

        Args:
            bk_biz_id: 业务 ID
            conf_list: 节点配置列表
        """
        return self._client.post(
            f"{self._base_path}/import/",
            json={"bk_biz_id": bk_biz_id, "conf_list": conf_list},
        )

    def export(self, bk_biz_id: int, node_ids: list[int] | None = None) -> ApiResponse[Any]:
        """
        导出拨测节点配置

        Args:
            bk_biz_id: 业务 ID
            node_ids: 节点 ID 列表（可选，不传则导出全部）
        """
        params: dict[str, Any] = {"bk_biz_id": bk_biz_id}
        if node_ids:
            params["node_ids"] = node_ids
        return self._client.get(f"{self._base_path}/export/", params=params)


class UptimeCheckTaskClient:
    """拨测任务 API 客户端"""

    def __init__(self, api_client: BaseApiClient) -> None:
        self._client = api_client
        self._base_path = "uptime_check/task"

    def list(
        self,
        bk_biz_id: int,
        task_id: int | None = None,
        group_id: int | None = None,
        name: str | None = None,
        plain: bool = True,
        get_available: bool = False,
        get_task_duration: bool = False,
    ) -> ApiResponse[Any]:
        """
        获取拨测任务列表

        Args:
            bk_biz_id: 业务 ID
            task_id: 任务 ID（可选，用于查询单个任务）
            group_id: 分组 ID（可选，筛选指定分组的任务）
            name: 任务名称（可选，模糊匹配）
            plain: 是否返回简单数据（默认 True，返回基础字段）
            get_available: 是否获取可用率
            get_task_duration: 是否获取响应时长
        """
        params: dict[str, Any] = {"bk_biz_id": bk_biz_id}
        if task_id is not None:
            params["id"] = task_id
        if group_id is not None:
            params["group_id"] = group_id
        if name is not None:
            params["name"] = name
        if plain:
            params["plain"] = "true"
        if get_available:
            params["get_available"] = "true"
        if get_task_duration:
            params["get_task_duration"] = "true"
        return self._client.get(f"{self._base_path}/list/", params=params)

    def get(self, bk_biz_id: int, task_id: int) -> ApiResponse[Any]:
        """
        获取单个拨测任务详情

        Args:
            bk_biz_id: 业务 ID
            task_id: 任务 ID
        """
        return self.list(bk_biz_id=bk_biz_id, task_id=task_id, plain=True)

    def add(
        self,
        bk_biz_id: int,
        name: str,
        protocol: str,
        config: HttpTaskConfig | TcpUdpTaskConfig | IcmpTaskConfig | dict[str, Any],
        check_interval: int = 60,
        node_id_list: list[int] | None = None,
        groups: list[int] | None = None,
        **kwargs: Any,
    ) -> ApiResponse[Any]:
        """
        新增拨测任务

        Args:
            bk_biz_id: 业务 ID
            name: 任务名称
            protocol: 协议类型 (HTTP/TCP/UDP/ICMP)
            config: 任务配置
            check_interval: 检测间隔(秒)
            node_id_list: 执行节点 ID 列表
            groups: 所属分组 ID 列表
        """
        # 处理 config
        if isinstance(config, dict):
            config_data = config
        else:
            config_data = config.model_dump(exclude_none=True)

        request_data = {
            "bk_biz_id": bk_biz_id,
            "name": name,
            "protocol": protocol,
            "config": config_data,
            "check_interval": check_interval,
            "node_id_list": node_id_list or [],
            "groups": groups or [],
            **kwargs,
        }
        return self._client.post(f"{self._base_path}/create/", json=request_data)

    def edit(
        self,
        bk_biz_id: int,
        id: int,
        name: str | None = None,
        config: HttpTaskConfig | TcpUdpTaskConfig | IcmpTaskConfig | dict[str, Any] | None = None,
        check_interval: int | None = None,
        node_id_list: list[int] | None = None,
        groups: list[int] | None = None,
        **kwargs: Any,
    ) -> ApiResponse[Any]:
        """
        编辑拨测任务

        Args:
            bk_biz_id: 业务 ID
            id: 任务 ID
            name: 任务名称
            config: 任务配置
            check_interval: 检测间隔(秒)
            node_id_list: 执行节点 ID 列表
            groups: 所属分组 ID 列表
        """
        # 注意：API 网关期望的参数名是 task_id，不是 id
        request_data: dict[str, Any] = {"bk_biz_id": bk_biz_id, "task_id": id}

        if name is not None:
            request_data["name"] = name
        if config is not None:
            if isinstance(config, dict):
                request_data["config"] = config
            else:
                request_data["config"] = config.model_dump(exclude_none=True)
        if check_interval is not None:
            request_data["check_interval"] = check_interval
        if node_id_list is not None:
            request_data["node_id_list"] = node_id_list
        if groups is not None:
            request_data["groups"] = groups

        request_data.update(kwargs)
        return self._client.post(f"{self._base_path}/edit/", json=request_data)

    def delete(self, bk_biz_id: int, id: int) -> ApiResponse[Any]:
        """
        删除拨测任务

        Args:
            bk_biz_id: 业务 ID
            id: 任务 ID
        """
        data = UptimeCheckTaskDelete(bk_biz_id=bk_biz_id, id=id)
        return self._client.post(f"{self._base_path}/delete/", json=data.model_dump(by_alias=True))

    def deploy(self, bk_biz_id: int, id: int) -> ApiResponse[Any]:
        """
        部署拨测任务

        Args:
            bk_biz_id: 业务 ID
            id: 任务 ID
        """
        data = UptimeCheckTaskDeploy(bk_biz_id=bk_biz_id, id=id)
        return self._client.post(f"{self._base_path}/deploy/", json=data.model_dump(by_alias=True))

    def change_status(self, bk_biz_id: int, id: int, status: str) -> ApiResponse[Any]:
        """
        更改拨测任务状态

        Args:
            bk_biz_id: 业务 ID
            id: 任务 ID
            status: 目标状态 (running/stoped)
        """
        data = UptimeCheckTaskChangeStatus(bk_biz_id=bk_biz_id, id=id, status=status)  # type: ignore
        return self._client.post(f"{self._base_path}/change_status/", json=data.model_dump(by_alias=True))


class UptimeCheckTaskCollectorClient:
    """拨测任务导入导出客户端"""

    def __init__(self, api_client: BaseApiClient) -> None:
        self._client = api_client
        self._base_path = "uptime_check/task"

    def import_tasks(self, bk_biz_id: int, conf_list: list[dict[str, Any]]) -> ApiResponse[Any]:
        """
        导入拨测任务

        Args:
            bk_biz_id: 业务 ID
            conf_list: 任务配置列表
        """
        return self._client.post(
            f"{self._base_path}/import/",
            json={"bk_biz_id": bk_biz_id, "conf_list": conf_list},
        )

    def export(self, bk_biz_id: int, task_ids: list[int] | None = None) -> ApiResponse[Any]:
        """
        导出拨测任务配置

        Args:
            bk_biz_id: 业务 ID
            task_ids: 任务 ID 列表（可选，不传则导出全部）
        """
        params: dict[str, Any] = {"bk_biz_id": bk_biz_id}
        if task_ids:
            params["task_ids"] = task_ids
        return self._client.get(f"{self._base_path}/export/", params=params)


class UptimeCheckGroupClient:
    """拨测分组 API 客户端"""

    def __init__(self, api_client: BaseApiClient) -> None:
        self._client = api_client
        self._base_path = "uptime_check/group"

    def list(self, bk_biz_id: int) -> ApiResponse[Any]:
        """
        获取拨测分组列表

        Args:
            bk_biz_id: 业务 ID

        Returns:
            包含分组列表的响应，每个分组包含 id, name, logo, task_ids 等字段
        """
        return self._client.get(f"{self._base_path}/list/", params={"bk_biz_id": bk_biz_id})

    def add(self, bk_biz_id: int, name: str, logo: str = "") -> ApiResponse[Any]:
        """
        新增拨测分组

        Args:
            bk_biz_id: 业务 ID
            name: 分组名称
            logo: 分组图标
        """
        data = UptimeCheckGroupCreate(bk_biz_id=bk_biz_id, name=name, logo=logo)
        return self._client.post(f"{self._base_path}/create/", json=data.model_dump())

    def edit(
        self,
        bk_biz_id: int,
        id: int,
        name: str | None = None,
        logo: str | None = None,
    ) -> ApiResponse[Any]:
        """
        编辑拨测分组

        Args:
            bk_biz_id: 业务 ID
            id: 分组 ID
            name: 分组名称
            logo: 分组图标
        """
        data = UptimeCheckGroupUpdate(bk_biz_id=bk_biz_id, id=id, name=name, logo=logo)
        return self._client.post(f"{self._base_path}/edit/", json=data.model_dump(exclude_none=True, by_alias=True))

    def delete(self, bk_biz_id: int, id: int) -> ApiResponse[Any]:
        """
        删除拨测分组

        Args:
            bk_biz_id: 业务 ID
            id: 分组 ID
        """
        data = UptimeCheckGroupDelete(bk_biz_id=bk_biz_id, id=id)
        return self._client.post(f"{self._base_path}/delete/", json=data.model_dump(by_alias=True))

    def add_task(self, bk_biz_id: int, id: int, task_id: int) -> ApiResponse[Any]:
        """
        添加任务到分组

        Args:
            bk_biz_id: 业务 ID
            id: 分组 ID
            task_id: 任务 ID
        """
        data = UptimeCheckGroupAddTask(bk_biz_id=bk_biz_id, id=id, task_id=task_id)
        return self._client.post(f"{self._base_path}/add_task/", json=data.model_dump(by_alias=True))

    def remove_task(self, bk_biz_id: int, id: int, task_id: int) -> ApiResponse[Any]:
        """
        从分组移除任务

        Args:
            bk_biz_id: 业务 ID
            id: 分组 ID
            task_id: 任务 ID
        """
        data = UptimeCheckGroupRemoveTask(bk_biz_id=bk_biz_id, id=id, task_id=task_id)
        return self._client.post(f"{self._base_path}/remove_task/", json=data.model_dump(by_alias=True))


class UptimeCheckClient:
    """
    拨测统一客户端

    聚合节点、任务、分组的所有操作
    """

    def __init__(self, settings: Settings) -> None:
        """
        初始化客户端

        Args:
            settings: 全局配置对象
        """
        self._api_client = BaseApiClient(settings)
        self.settings = settings

        # 初始化子客户端
        self.node = UptimeCheckNodeClient(self._api_client)
        self.node_collector = UptimeCheckNodeCollectorClient(self._api_client)
        self.task = UptimeCheckTaskClient(self._api_client)
        self.task_collector = UptimeCheckTaskCollectorClient(self._api_client)
        self.group = UptimeCheckGroupClient(self._api_client)

    @property
    def bk_biz_id(self) -> int:
        """获取默认业务 ID"""
        return self.settings.biz.bk_biz_id
