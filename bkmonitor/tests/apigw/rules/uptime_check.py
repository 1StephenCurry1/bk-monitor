"""
拨测模块（Uptime Check）API 响应校验规则
API 返回结构说明：
- node.add/edit 返回完整节点信息（包含 bk_tenant_id, location 等）
- node.list 返回简化的节点列表（包含 country, province 替代 location）
- group.add/edit 返回完整分组信息
- task.add/edit 返回完整任务信息
- task.list (plain=True) 返回简化任务列表
- delete 接口返回 {id, result} 或 {group_id, result}
"""

from __future__ import annotations

from tests.apigw.utils.response_validator import (
    FieldRule,
    expect_values,
    field_equals,
    field_in,
)


class UptimeCheckRules:
    """
    拨测模块专用校验规则集合

    提供 Node、Group、Task 三种资源的响应校验规则

    Example:
        >>> from tests.apigw.rules import UptimeCheckRules
        >>> rules = UptimeCheckRules.node_response(
        ...     expected_name="test_node",
        ...     expected_ip="10.0.0.1",
        ...     expected_bk_cloud_id=0,
        ...     expected_bk_biz_id=2,
        ... )
    """

    # ==================== Node 相关规则 ====================

    @staticmethod
    def node_response(
        expected_name: str,
        expected_ip: str,
        expected_bk_cloud_id: int,
        expected_bk_biz_id: int,
        expected_ip_type: int = 4,
        expected_carrieroperator: str = "内网",
        expected_is_common: bool = False,
        expected_bk_host_id: int | None = None,
        expected_location: dict | None = None,
    ) -> list[FieldRule]:
        """
        UptimeCheckNode 创建/更新响应完整校验规则

        基于实际 API 返回结构（node.add/edit）：
        {
            "bk_tenant_id": str,       # 租户 ID
            "bk_biz_id": int,          # 业务 ID
            "id": int,                 # 节点 ID
            "name": str,               # 节点名称
            "is_common": bool,         # 是否为通用节点
            "biz_scope": list,         # 业务可见范围
            "ip_type": int,            # IP 类型（0/4/6）
            "bk_host_id": int,         # 主机 ID
            "ip": str,                 # IP 地址
            "bk_cloud_id": int,        # 云区域 ID
            "location": dict,          # 地区信息 {"country": str, "city": str}
            "carrieroperator": str,    # 运营商
            "create_user": str,        # 创建人
            "create_time": str,        # 创建时间
            "update_user": str,        # 更新人
            "update_time": str,        # 更新时间
        }

        Args:
            expected_name: 期望的节点名称
            expected_ip: 期望的 IP 地址
            expected_bk_cloud_id: 期望的云区域 ID
            expected_bk_biz_id: 期望的业务 ID
            expected_ip_type: 期望的 IP 类型（0/4/6）
            expected_carrieroperator: 期望的运营商
            expected_is_common: 期望是否为通用节点
            expected_bk_host_id: 期望的主机 ID
            expected_location: 期望的地区信息
        """
        rules: list[FieldRule] = [
            # ===== 必填字段（类型校验）=====
            FieldRule(path="$.data.id", required=True, expected_type=int),
            FieldRule(path="$.data.bk_tenant_id", required=True, expected_type=str),
            FieldRule(path="$.data.bk_biz_id", required=True, expected_type=int),
            FieldRule(path="$.data.name", required=True, expected_type=str),
            FieldRule(path="$.data.is_common", required=True, expected_type=bool),
            FieldRule(path="$.data.biz_scope", required=True, expected_type=list),
            FieldRule(path="$.data.ip_type", required=True, expected_type=int),
            FieldRule(path="$.data.ip", required=True, expected_type=str),
            FieldRule(path="$.data.bk_cloud_id", required=True, expected_type=int),
            FieldRule(path="$.data.location", required=True, expected_type=dict),
            FieldRule(path="$.data.carrieroperator", required=True, expected_type=str),
            FieldRule(path="$.data.create_time", required=True, expected_type=str),
            FieldRule(path="$.data.update_time", required=True, expected_type=str),
            FieldRule(path="$.data.create_user", required=True, expected_type=str),
            FieldRule(path="$.data.update_user", required=True, expected_type=str),
        ]

        # 精确值校验
        value_rules = expect_values(
            {
                "$.data.name": expected_name,
                "$.data.ip": expected_ip,
                "$.data.bk_cloud_id": expected_bk_cloud_id,
                "$.data.bk_biz_id": expected_bk_biz_id,
                "$.data.ip_type": expected_ip_type,
                "$.data.carrieroperator": expected_carrieroperator,
                "$.data.is_common": expected_is_common,
            }
        )
        rules.extend(value_rules)

        # 可选字段精确值校验
        if expected_bk_host_id is not None:
            rules.append(field_equals("$.data.bk_host_id", expected_bk_host_id))

        if expected_location is not None:
            rules.append(field_equals("$.data.location", expected_location))

        # ip_type 枚举校验
        rules.append(field_in("$.data.ip_type", [0, 4, 6], "IP 类型必须是 0/4/6"))

        return rules

    @staticmethod
    def node_response_types_only() -> list[FieldRule]:
        """
        UptimeCheckNode 创建/更新响应仅类型校验（不校验具体值）

        用于不关心具体值的场景
        """
        return [
            # 必填字段类型校验
            FieldRule(path="$.data.id", required=True, expected_type=int),
            FieldRule(path="$.data.bk_tenant_id", required=True, expected_type=str),
            FieldRule(path="$.data.bk_biz_id", required=True, expected_type=int),
            FieldRule(path="$.data.name", required=True, expected_type=str),
            FieldRule(path="$.data.is_common", required=True, expected_type=bool),
            FieldRule(path="$.data.biz_scope", required=True, expected_type=list),
            FieldRule(path="$.data.ip_type", required=True, expected_type=int),
            FieldRule(path="$.data.ip", required=True, expected_type=str),
            FieldRule(path="$.data.bk_cloud_id", required=True, expected_type=int),
            FieldRule(path="$.data.location", required=True, expected_type=dict),
            FieldRule(path="$.data.carrieroperator", required=True, expected_type=str),
            FieldRule(path="$.data.create_time", required=True, expected_type=str),
            FieldRule(path="$.data.update_time", required=True, expected_type=str),
            # 枚举校验
            field_in("$.data.ip_type", [0, 4, 6], "IP 类型必须是 0/4/6"),
        ]

    @staticmethod
    def node_list_item() -> list[FieldRule]:
        """
        UptimeCheckNode 列表项校验规则
        {
            "id": int,                 # 节点 ID
            "bk_biz_id": int,          # 业务 ID
            "name": str,               # 节点名称
            "ip": str,                 # IP 地址
            "bk_host_id": int,         # 主机 ID
            "bk_cloud_id": int,        # 云区域 ID
            "ip_type": int,            # IP 类型
            "country": str,            # 国家
            "province": str,           # 省份
            "carrieroperator": str,    # 运营商
            "task_num": int,           # 关联任务数
            "is_common": bool,         # 是否为通用节点
            "gse_status": str,         # GSE 状态
            "status": str,             # 节点状态
            "version": str,            # 版本
        }
        """
        return [
            FieldRule(path="$.id", required=True, expected_type=int),
            FieldRule(path="$.bk_biz_id", required=True, expected_type=int),
            FieldRule(path="$.name", required=True, expected_type=str),
            FieldRule(path="$.ip", required=True, expected_type=str),
            FieldRule(path="$.bk_host_id", required=True, expected_type=int),
            FieldRule(path="$.bk_cloud_id", required=True, expected_type=int),
            FieldRule(path="$.ip_type", required=True, expected_type=int),
            FieldRule(path="$.country", required=True, expected_type=str),
            FieldRule(path="$.province", required=True, expected_type=str),
            FieldRule(path="$.carrieroperator", required=True, expected_type=str),
            FieldRule(path="$.task_num", required=True, expected_type=int),
            FieldRule(path="$.is_common", required=True, expected_type=bool),
            FieldRule(path="$.gse_status", required=True, expected_type=str),
            FieldRule(path="$.status", required=True, expected_type=str),
            FieldRule(path="$.version", required=True, expected_type=str),
            # 枚举校验
            field_in("$.ip_type", [0, 4, 6], "IP 类型必须是 0/4/6"),
        ]

    @staticmethod
    def node_delete_response() -> list[FieldRule]:
        """
        UptimeCheckNode 删除响应校验规则

        基于实际 API 返回结构：
        {
            "id": int,                 # 被删除的节点 ID
            "result": str,             # 删除结果 "删除成功"
        }
        """
        return [
            FieldRule(path="$.data.id", required=True, expected_type=int),
            FieldRule(path="$.data.result", required=True, expected_type=str),
        ]

    # ==================== Group 相关规则 ====================

    @staticmethod
    def group_response(
        expected_name: str,
        expected_bk_biz_id: int,
    ) -> list[FieldRule]:
        """
        UptimeCheckGroup 创建/更新响应完整校验规则
        {
            "bk_tenant_id": str,       # 租户 ID
            "id": int,                 # 分组 ID
            "bk_biz_id": int,          # 业务 ID
            "name": str,               # 分组名称
            "logo": str,               # Logo
            "task_ids": list,          # 关联的任务 ID 列表
            "create_user": str,        # 创建人
            "create_time": str,        # 创建时间
            "update_user": str,        # 更新人
            "update_time": str,        # 更新时间
        }
        """
        return [
            # 必填字段类型校验
            FieldRule(path="$.data.id", required=True, expected_type=int),
            FieldRule(path="$.data.bk_tenant_id", required=True, expected_type=str),
            FieldRule(path="$.data.bk_biz_id", required=True, expected_type=int),
            FieldRule(path="$.data.name", required=True, expected_type=str),
            FieldRule(path="$.data.logo", required=True, expected_type=str),
            FieldRule(path="$.data.task_ids", required=True, expected_type=list),
            FieldRule(path="$.data.create_time", required=True, expected_type=str),
            FieldRule(path="$.data.update_time", required=True, expected_type=str),
            FieldRule(path="$.data.create_user", required=True, expected_type=str),
            FieldRule(path="$.data.update_user", required=True, expected_type=str),
            # 精确值校验
            *expect_values(
                {
                    "$.data.name": expected_name,
                    "$.data.bk_biz_id": expected_bk_biz_id,
                }
            ),
        ]

    @staticmethod
    def group_list_item() -> list[FieldRule]:
        """
        UptimeCheckGroup 列表项校验规则（用于 group.list 返回的列表项）

        基于实际 API 返回结构：
        {
            "bk_tenant_id": str,       # 租户 ID
            "id": int,                 # 分组 ID
            "bk_biz_id": int,          # 业务 ID
            "name": str,               # 分组名称
            "logo": str,               # Logo
            "tasks": list,             # 关联的任务列表
            "create_user": str,        # 创建人
            "create_time": str,        # 创建时间
            "update_user": str,        # 更新人
            "update_time": str,        # 更新时间
        }
        """
        return [
            FieldRule(path="$.id", required=True, expected_type=int),
            FieldRule(path="$.bk_tenant_id", required=True, expected_type=str),
            FieldRule(path="$.bk_biz_id", required=True, expected_type=int),
            FieldRule(path="$.name", required=True, expected_type=str),
            FieldRule(path="$.logo", required=True, expected_type=str),
            FieldRule(path="$.tasks", required=True, expected_type=list),
            FieldRule(path="$.create_time", required=True, expected_type=str),
            FieldRule(path="$.update_time", required=True, expected_type=str),
            FieldRule(path="$.create_user", required=True, expected_type=str),
            FieldRule(path="$.update_user", required=True, expected_type=str),
        ]

    @staticmethod
    def group_delete_response() -> list[FieldRule]:
        """
        UptimeCheckGroup 删除响应校验规则

        基于实际 API 返回结构：
        {
            "group_id": int,           # 被删除的分组 ID
            "result": str,             # 删除结果 "删除成功"
        }
        """
        return [
            FieldRule(path="$.data.group_id", required=True, expected_type=int),
            FieldRule(path="$.data.result", required=True, expected_type=str),
        ]

    @staticmethod
    def group_add_task_response() -> list[FieldRule]:
        """
        UptimeCheckGroup 添加任务响应校验规则

        基于实际 API 返回结构：
        {
            "msg": str,                # 操作消息
        }
        """
        return [
            FieldRule(path="$.data.msg", required=True, expected_type=str),
        ]

    @staticmethod
    def group_remove_task_response() -> list[FieldRule]:
        """
        UptimeCheckGroup 移除任务响应校验规则

        基于实际 API 返回结构：
        {
            "msg": str,                # 操作消息
        }
        """
        return [
            FieldRule(path="$.data.msg", required=True, expected_type=str),
        ]

    # ==================== Task 相关规则 ====================

    @staticmethod
    def task_response(
        expected_name: str,
        expected_protocol: str,
        expected_bk_biz_id: int,
    ) -> list[FieldRule]:
        """
        UptimeCheckTask 创建/更新响应完整校验规则

        基于实际 API 返回结构（task.add/edit）：
        {
            "bk_tenant_id": str,       # 租户 ID
            "id": int,                 # 任务 ID
            "bk_biz_id": int,          # 业务 ID
            "name": str,               # 任务名称
            "protocol": str,           # 协议（HTTP/TCP/UDP/ICMP）
            "config": dict,            # 任务配置
            "labels": dict,            # 标签
            "independent_dataid": bool,# 是否独立数据 ID
            "check_interval": int,     # 检查间隔
            "location": dict,          # 地区信息 {"country": str, "city": str}
            "node_ids": list,          # 节点 ID 列表
            "group_ids": list,         # 分组 ID 列表
            "status": str,             # 任务状态
            "create_user": str,        # 创建人
            "create_time": str,        # 创建时间
            "update_user": str,        # 更新人
            "update_time": str,        # 更新时间
        }
        """
        return [
            # 必填字段类型校验
            FieldRule(path="$.data.id", required=True, expected_type=int),
            FieldRule(path="$.data.bk_tenant_id", required=True, expected_type=str),
            FieldRule(path="$.data.bk_biz_id", required=True, expected_type=int),
            FieldRule(path="$.data.name", required=True, expected_type=str),
            FieldRule(path="$.data.protocol", required=True, expected_type=str),
            FieldRule(path="$.data.config", required=True, expected_type=dict),
            FieldRule(path="$.data.labels", required=True, expected_type=dict),
            FieldRule(path="$.data.independent_dataid", required=True, expected_type=bool),
            FieldRule(path="$.data.check_interval", required=True, expected_type=int),
            FieldRule(path="$.data.location", required=True, expected_type=dict),
            FieldRule(path="$.data.node_ids", required=True, expected_type=list),
            FieldRule(path="$.data.group_ids", required=True, expected_type=list),
            FieldRule(path="$.data.status", required=True, expected_type=str),
            FieldRule(path="$.data.create_time", required=True, expected_type=str),
            FieldRule(path="$.data.update_time", required=True, expected_type=str),
            FieldRule(path="$.data.create_user", required=True, expected_type=str),
            FieldRule(path="$.data.update_user", required=True, expected_type=str),
            # 精确值校验
            *expect_values(
                {
                    "$.data.name": expected_name,
                    "$.data.protocol": expected_protocol,
                    "$.data.bk_biz_id": expected_bk_biz_id,
                }
            ),
            # 协议枚举校验
            field_in("$.data.protocol", ["HTTP", "TCP", "UDP", "ICMP"]),
        ]

    @staticmethod
    def task_response_types_only() -> list[FieldRule]:
        """
        UptimeCheckTask 创建/更新响应仅类型校验（不校验具体值）
        """
        return [
            FieldRule(path="$.data.id", required=True, expected_type=int),
            FieldRule(path="$.data.bk_tenant_id", required=True, expected_type=str),
            FieldRule(path="$.data.bk_biz_id", required=True, expected_type=int),
            FieldRule(path="$.data.name", required=True, expected_type=str),
            FieldRule(path="$.data.protocol", required=True, expected_type=str),
            FieldRule(path="$.data.config", required=True, expected_type=dict),
            FieldRule(path="$.data.labels", required=True, expected_type=dict),
            FieldRule(path="$.data.independent_dataid", required=True, expected_type=bool),
            FieldRule(path="$.data.check_interval", required=True, expected_type=int),
            FieldRule(path="$.data.location", required=True, expected_type=dict),
            FieldRule(path="$.data.node_ids", required=True, expected_type=list),
            FieldRule(path="$.data.group_ids", required=True, expected_type=list),
            FieldRule(path="$.data.status", required=True, expected_type=str),
            FieldRule(path="$.data.create_time", required=True, expected_type=str),
            FieldRule(path="$.data.update_time", required=True, expected_type=str),
            # 协议枚举校验
            field_in("$.data.protocol", ["HTTP", "TCP", "UDP", "ICMP"]),
        ]

    @staticmethod
    def task_list_item() -> list[FieldRule]:
        """
        UptimeCheckTask 列表项校验规则（plain=True 模式）

        基于实际 API 返回结构（task.list with plain=True）：
        {
            "id": int,                 # 任务 ID
            "name": str,               # 任务名称
            "bk_biz_id": int,          # 业务 ID
        }

        注意：plain=True 时返回简化结构
        """
        return [
            FieldRule(path="$.id", required=True, expected_type=int),
            FieldRule(path="$.name", required=True, expected_type=str),
            FieldRule(path="$.bk_biz_id", required=True, expected_type=int),
        ]

    @staticmethod
    def task_list_item_full() -> list[FieldRule]:
        """
        UptimeCheckTask 列表项校验规则（plain=False 或 task.get 单任务查询模式）

        基于实际 API 返回结构（task.list with plain=False 或 task.get）：
        {
            "id": int,                 # 任务 ID
            "name": str,               # 任务名称
            "bk_biz_id": int,          # 业务 ID
            "protocol": str,           # 协议
            "config": dict,            # 任务配置
            "node_ids": list,          # 节点 ID 列表
            "group_ids": list,         # 分组 ID 列表
            "status": str,             # 任务状态
        }
        """
        return [
            FieldRule(path="$.id", required=True, expected_type=int),
            FieldRule(path="$.name", required=True, expected_type=str),
            FieldRule(path="$.bk_biz_id", required=True, expected_type=int),
            FieldRule(path="$.protocol", required=True, expected_type=str),
            FieldRule(path="$.config", required=True, expected_type=dict),
            FieldRule(path="$.node_ids", required=True, expected_type=list),
            FieldRule(path="$.group_ids", required=True, expected_type=list),
            FieldRule(path="$.status", required=True, expected_type=str),
            # 协议枚举校验
            field_in("$.protocol", ["HTTP", "TCP", "UDP", "ICMP"]),
        ]

    @staticmethod
    def task_delete_response() -> list[FieldRule]:
        """
        UptimeCheckTask 删除响应校验规则

        基于实际 API 返回结构：
        {
            "id": int,                 # 被删除的任务 ID
            "result": str,             # 删除结果 "删除成功"
        }
        """
        return [
            FieldRule(path="$.data.id", required=True, expected_type=int),
            FieldRule(path="$.data.result", required=True, expected_type=str),
        ]

    @staticmethod
    def task_deploy_response() -> list[FieldRule]:
        """
        UptimeCheckTask 部署响应校验规则

        基于实际 API 返回结构：
        data: "success"
        """
        return [
            FieldRule(path="$.data", required=True, expected_type=str),
            field_equals("$.data", "success"),
        ]

    @staticmethod
    def task_change_status_response() -> list[FieldRule]:
        """
        UptimeCheckTask 状态变更响应校验规则

        注意：此接口需要 operator 参数，否则返回错误
        """
        return [
            FieldRule(path="$.result", required=True, expected_type=bool),
        ]

    # ==================== Export 相关规则 ====================

    @staticmethod
    def node_export_response() -> list[FieldRule]:
        """
        UptimeCheckNode 导出响应校验规则

        基于实际 API 返回结构（node_collector.export）：
        [
            {
                "target_conf": dict,       # 目标配置
                "collector_conf": dict,    # 采集器配置
                "plugin_info": dict,       # 插件信息
            }
        ]

        返回值为列表，每个元素对应一个节点的导出配置
        """
        return [
            FieldRule(path="$.data", required=True, expected_type=list),
        ]

    @staticmethod
    def task_export_response() -> list[FieldRule]:
        """
        UptimeCheckTask 导出响应校验规则

        基于实际 API 返回结构（task_collector.export）：
        [
            {
                "target_conf": dict,       # 目标配置
                "collector_conf": dict,    # 采集器配置
                "monitor_conf": list,      # 监控配置
            }
        ]

        返回值为列表，每个元素对应一个任务的导出配置
        """
        return [
            FieldRule(path="$.data", required=True, expected_type=list),
        ]

    @staticmethod
    def task_export_item() -> list[FieldRule]:
        """
        UptimeCheckTask 导出项校验规则
        """
        return [
            FieldRule(path="$.target_conf", required=True, expected_type=dict),
            FieldRule(path="$.collector_conf", required=True, expected_type=dict),
            FieldRule(path="$.monitor_conf", required=True, expected_type=list),
        ]
