"""
拨测数据模型

定义拨测节点、任务、分组的请求和响应数据结构
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


# ============== 拨测节点模型 ==============


class UptimeCheckNodeCreate(BaseModel):
    """创建拨测节点请求"""

    bk_biz_id: int = Field(description="业务 ID")
    name: str = Field(description="节点名称")
    ip: str = Field(description="节点 IP")
    bk_cloud_id: int = Field(default=0, description="云区域 ID")
    plat_id: int = Field(default=0, description="云区域 ID（兼容旧字段名）")
    is_common: bool = Field(default=False, description="是否为公共节点")
    location: dict[str, Any] = Field(default_factory=dict, description="地理位置")
    carrieroperator: str = Field(default="内网", description="运营商")
    ip_type: int = Field(default=4, description="IP 类型（0=ALL, 4=IPv4, 6=IPv6）")
    bk_host_id: int | None = Field(default=None, description="主机 ID")


class UptimeCheckNodeUpdate(BaseModel):
    """更新拨测节点请求"""

    bk_biz_id: int = Field(description="业务 ID")
    id: int = Field(description="节点 ID", serialization_alias="node_id")
    name: str | None = Field(default=None, description="节点名称")
    is_common: bool | None = Field(default=None, description="是否为公共节点")
    location: dict[str, Any] | None = Field(default=None, description="地理位置")
    carrieroperator: str | None = Field(default=None, description="运营商")

    model_config = {"populate_by_name": True}


class UptimeCheckNodeDelete(BaseModel):
    """删除拨测节点请求"""

    bk_biz_id: int = Field(description="业务 ID")
    id: int = Field(description="节点 ID", serialization_alias="node_id")

    model_config = {"populate_by_name": True}


class UptimeCheckNodeData(BaseModel):
    """拨测节点数据"""

    id: int = Field(description="节点 ID")
    bk_biz_id: int = Field(description="业务 ID")
    name: str = Field(description="节点名称")
    ip: str = Field(description="节点 IP")
    bk_cloud_id: int = Field(default=0, description="云区域 ID")
    is_common: bool = Field(default=False, description="是否为公共节点")
    location: dict[str, Any] = Field(default_factory=dict, description="地理位置")
    carrieroperator: str = Field(default="", description="运营商")


# ============== 拨测任务模型 ==============


class HttpTaskConfig(BaseModel):
    """HTTP 任务配置"""

    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"] = Field(default="GET", description="HTTP 方法")
    urls: str = Field(description="目标 URL（多个用换行分隔）")
    headers: list[dict[str, str]] = Field(default_factory=list, description="请求头")
    body: dict[str, Any] | None = Field(default=None, description="请求体")
    response_code: str = Field(default="", description="期望响应码")
    response: str = Field(default="", description="期望响应内容")
    insecure_skip_verify: bool = Field(default=False, description="跳过 SSL 验证")
    request_timeout: int = Field(default=3000, description="请求超时时间(ms)")


class TcpUdpTaskConfig(BaseModel):
    """TCP/UDP 任务配置"""

    ip_list: list[str] = Field(default_factory=list, description="目标 IP 列表")
    port: int = Field(description="目标端口")
    response: str = Field(default="", description="期望响应内容")
    response_format: Literal["in", "eq", "reg", ""] = Field(default="", description="响应匹配格式")
    request_timeout: int = Field(default=3000, description="请求超时时间(ms)")


class IcmpTaskConfig(BaseModel):
    """ICMP 任务配置"""

    ip_list: list[str] = Field(default_factory=list, description="目标 IP 列表")
    max_rtt: int = Field(default=3000, description="最大 RTT(ms)")
    total_num: int = Field(default=3, description="探测次数")
    size: int = Field(default=56, description="数据包大小")


class UptimeCheckTaskCreate(BaseModel):
    """创建拨测任务请求"""

    bk_biz_id: int = Field(description="业务 ID")
    name: str = Field(description="任务名称")
    protocol: Literal["HTTP", "TCP", "UDP", "ICMP"] = Field(description="协议类型")
    check_interval: int = Field(default=60, description="检测间隔(秒)")
    node_id_list: list[int] = Field(default_factory=list, description="执行节点 ID 列表")
    # 根据 protocol 选择对应的配置
    config: HttpTaskConfig | TcpUdpTaskConfig | IcmpTaskConfig = Field(description="任务配置")
    # 可选字段
    groups: list[int] = Field(default_factory=list, description="所属分组 ID 列表")
    timeout: int = Field(default=3000, description="超时时间(ms)")
    period: int = Field(default=60, description="检测周期(秒)")
    available_duration: int = Field(default=60, description="可用时长(秒)")


class UptimeCheckTaskUpdate(BaseModel):
    """更新拨测任务请求"""

    bk_biz_id: int = Field(description="业务 ID")
    id: int = Field(description="任务 ID")
    name: str | None = Field(default=None, description="任务名称")
    check_interval: int | None = Field(default=None, description="检测间隔(秒)")
    node_id_list: list[int] | None = Field(default=None, description="执行节点 ID 列表")
    config: HttpTaskConfig | TcpUdpTaskConfig | IcmpTaskConfig | None = Field(default=None, description="任务配置")
    groups: list[int] | None = Field(default=None, description="所属分组 ID 列表")


class UptimeCheckTaskDelete(BaseModel):
    """删除拨测任务请求"""

    bk_biz_id: int = Field(description="业务 ID")
    id: int = Field(description="任务 ID", serialization_alias="task_id")

    model_config = {"populate_by_name": True}


class UptimeCheckTaskDeploy(BaseModel):
    """部署拨测任务请求"""

    bk_biz_id: int = Field(description="业务 ID")
    id: int = Field(description="任务 ID", serialization_alias="task_id")

    model_config = {"populate_by_name": True}


class UptimeCheckTaskChangeStatus(BaseModel):
    """更改拨测任务状态请求"""

    bk_biz_id: int = Field(description="业务 ID")
    id: int = Field(description="任务 ID", serialization_alias="task_id")
    status: Literal["running", "stoped"] = Field(description="目标状态")

    model_config = {"populate_by_name": True}


class UptimeCheckTaskData(BaseModel):
    """拨测任务数据"""

    id: int = Field(description="任务 ID")
    bk_biz_id: int = Field(description="业务 ID")
    name: str = Field(description="任务名称")
    protocol: str = Field(description="协议类型")
    check_interval: int = Field(default=60, description="检测间隔(秒)")
    status: str = Field(default="", description="任务状态")
    node_id_list: list[int] = Field(default_factory=list, description="执行节点 ID 列表")
    config: dict[str, Any] = Field(default_factory=dict, description="任务配置")
    groups: list[int] = Field(default_factory=list, description="所属分组 ID 列表")


# ============== 拨测分组模型 ==============


class UptimeCheckGroupCreate(BaseModel):
    """创建拨测分组请求"""

    bk_biz_id: int = Field(description="业务 ID")
    name: str = Field(description="分组名称")
    logo: str = Field(default="", description="分组图标")


class UptimeCheckGroupUpdate(BaseModel):
    """更新拨测分组请求"""

    bk_biz_id: int = Field(description="业务 ID")
    id: int = Field(description="分组 ID", serialization_alias="group_id")
    name: str | None = Field(default=None, description="分组名称")
    logo: str | None = Field(default=None, description="分组图标")

    model_config = {"populate_by_name": True}


class UptimeCheckGroupDelete(BaseModel):
    """删除拨测分组请求"""

    bk_biz_id: int = Field(description="业务 ID")
    id: int = Field(description="分组 ID", serialization_alias="group_id")

    model_config = {"populate_by_name": True}


class UptimeCheckGroupAddTask(BaseModel):
    """添加任务到分组请求"""

    bk_biz_id: int = Field(description="业务 ID")
    id: int = Field(description="分组 ID", serialization_alias="group_id")
    task_id: int = Field(description="任务 ID")

    model_config = {"populate_by_name": True}


class UptimeCheckGroupRemoveTask(BaseModel):
    """从分组移除任务请求"""

    bk_biz_id: int = Field(description="业务 ID")
    id: int = Field(description="分组 ID", serialization_alias="group_id")
    task_id: int = Field(description="任务 ID")

    model_config = {"populate_by_name": True}


class UptimeCheckGroupData(BaseModel):
    """拨测分组数据"""

    id: int = Field(description="分组 ID")
    bk_biz_id: int = Field(description="业务 ID")
    name: str = Field(description="分组名称")
    logo: str = Field(default="", description="分组图标")
    task_count: int = Field(default=0, description="任务数量")


# ============== 导入导出模型 ==============


class ImportUptimeCheckNodeRequest(BaseModel):
    """导入拨测节点请求"""

    bk_biz_id: int = Field(description="业务 ID")
    conf_list: list[dict[str, Any]] = Field(description="节点配置列表")


class ImportUptimeCheckTaskRequest(BaseModel):
    """导入拨测任务请求"""

    bk_biz_id: int = Field(description="业务 ID")
    conf_list: list[dict[str, Any]] = Field(description="任务配置列表")


class ExportUptimeCheckRequest(BaseModel):
    """导出拨测配置请求"""

    bk_biz_id: int = Field(description="业务 ID")
    task_ids: list[int] | None = Field(default=None, description="任务 ID 列表（可选）")
    node_ids: list[int] | None = Field(default=None, description="节点 ID 列表（可选）")
