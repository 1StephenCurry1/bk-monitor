"""
告警策略数据模型

定义告警策略的请求和响应数据结构，用于：
1. 规范 API 调用参数
2. 提供类型安全和自动校验
3. 支持 IDE 自动补全
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


# ============== 查询配置模型 ==============


class AlarmStrategyQueryConfig(BaseModel):
    """告警策略查询配置"""

    data_source_label: str = Field(default="bk_monitor", description="数据源标签")
    data_type_label: str = Field(default="time_series", description="数据类型标签")
    alias: str = Field(default="a", description="别名")
    metric_id: str = Field(description="指标 ID")
    result_table_id: str = Field(description="结果表 ID")
    metric_field: str = Field(description="指标字段")
    unit: str = Field(default="", description="单位")
    agg_method: Literal["AVG", "SUM", "MAX", "MIN", "COUNT"] = Field(default="AVG", description="聚合方法")
    agg_interval: int = Field(default=60, description="聚合周期(秒)")
    agg_dimension: list[str] = Field(default_factory=list, description="聚合维度")
    agg_condition: list[dict[str, Any]] = Field(default_factory=list, description="聚合条件")
    functions: list[dict[str, Any]] = Field(default_factory=list, description="函数配置")


class AlarmStrategyAlgorithm(BaseModel):
    """告警策略检测算法"""

    type: Literal["Threshold", "SimpleRingRatio", "AdvancedRingRatio", "SimpleYearRound", "AdvancedYearRound"] = Field(
        default="Threshold", description="算法类型"
    )
    level: Literal[1, 2, 3] = Field(default=1, description="告警级别 (1=致命, 2=预警, 3=提醒)")
    config: list[list[dict[str, Any]]] = Field(description="算法配置")
    unit_prefix: str = Field(default="", description="单位前缀")


class AlarmStrategyNoDataConfig(BaseModel):
    """无数据配置"""

    continuous: int = Field(default=10, description="连续无数据周期数")
    is_enabled: bool = Field(default=False, description="是否启用无数据告警")
    agg_dimension: list[str] = Field(default_factory=list, description="聚合维度")


# ============== 策略配置项模型 ==============


class AlarmStrategyItem(BaseModel):
    """告警策略配置项"""

    name: str = Field(description="配置项名称")
    no_data_config: AlarmStrategyNoDataConfig = Field(
        default_factory=lambda: AlarmStrategyNoDataConfig(), description="无数据配置"
    )
    target: list[list[dict[str, Any]]] = Field(default_factory=list, description="监控目标")
    expression: str = Field(default="a", description="表达式")
    functions: list[dict[str, Any]] = Field(default_factory=list, description="函数配置")
    origin_sql: str = Field(default="", description="原始 SQL")
    query_configs: list[AlarmStrategyQueryConfig] = Field(description="查询配置列表")
    algorithms: list[AlarmStrategyAlgorithm] = Field(description="检测算法列表")


# ============== 检测配置模型 ==============


class AlarmStrategyUptimeConfig(BaseModel):
    """生效时间配置"""

    calendars: list[int] = Field(default_factory=list, description="日历 ID 列表")
    time_ranges: list[dict[str, str]] = Field(
        default_factory=lambda: [{"start": "00:00", "end": "23:59"}], description="时间范围"
    )


class AlarmStrategyTriggerConfig(BaseModel):
    """触发条件配置"""

    count: int = Field(default=3, description="触发次数")
    check_window: int = Field(default=5, description="检查窗口(周期数)")
    uptime: AlarmStrategyUptimeConfig = Field(default_factory=AlarmStrategyUptimeConfig, description="生效时间")


class AlarmStrategyRecoveryConfig(BaseModel):
    """恢复条件配置"""

    check_window: int = Field(default=5, description="检查窗口(周期数)")
    status_setter: Literal["recovery", "close"] = Field(default="recovery", description="恢复后状态")


class AlarmStrategyDetect(BaseModel):
    """检测配置"""

    level: Literal[1, 2, 3] = Field(default=1, description="告警级别")
    expression: str = Field(default="", description="检测表达式")
    trigger_config: AlarmStrategyTriggerConfig = Field(
        default_factory=AlarmStrategyTriggerConfig, description="触发条件"
    )
    recovery_config: AlarmStrategyRecoveryConfig = Field(
        default_factory=AlarmStrategyRecoveryConfig, description="恢复条件"
    )
    connector: Literal["and", "or"] = Field(default="and", description="连接符")


# ============== 通知配置模型 ==============


class AlarmStrategyConvergeConfig(BaseModel):
    """收敛配置"""

    is_enabled: bool = Field(default=True, description="是否启用收敛")
    converge_func: Literal["collect", "defense", "skip_when_success"] = Field(default="collect", description="收敛方式")
    timedelta: int = Field(default=60, description="收敛时间窗口(分钟)")
    count: int = Field(default=1, description="收敛次数")
    condition: list[dict[str, Any]] = Field(
        default_factory=lambda: [{"dimension": "strategy_id", "value": ["self"]}], description="收敛条件"
    )
    need_biz_converge: bool = Field(default=True, description="是否需要业务级收敛")


class AlarmStrategyNoticeOptions(BaseModel):
    """通知选项"""

    converge_config: AlarmStrategyConvergeConfig = Field(
        default_factory=AlarmStrategyConvergeConfig, description="收敛配置"
    )
    start_time: str = Field(default="00:00:00", description="生效开始时间")
    end_time: str = Field(default="23:59:59", description="生效结束时间")


class AlarmStrategyNoticeConfig(BaseModel):
    """通知内容配置"""

    interval_notify_mode: Literal["standard", "increasing"] = Field(default="standard", description="通知间隔模式")
    notify_interval: int = Field(default=7200, description="通知间隔(秒)")
    template: list[dict[str, Any]] = Field(default_factory=list, description="通知模板")


class AlarmStrategyNotice(BaseModel):
    """通知配置"""

    config_id: int = Field(default=0, description="配置 ID")
    user_groups: list[int] = Field(default_factory=list, description="通知组 ID 列表")
    signal: list[Literal["abnormal", "recovered", "closed", "no_data", "ack"]] = Field(
        default_factory=lambda: ["abnormal", "recovered"], description="通知信号"
    )
    options: AlarmStrategyNoticeOptions = Field(default_factory=AlarmStrategyNoticeOptions, description="通知选项")
    config: AlarmStrategyNoticeConfig = Field(default_factory=AlarmStrategyNoticeConfig, description="通知内容配置")


# ============== 策略请求模型 ==============


class AlarmStrategySearch(BaseModel):
    """查询告警策略请求"""

    bk_biz_id: int = Field(description="业务 ID")
    page: int = Field(default=1, description="页码")
    page_size: int = Field(default=10, description="每页数量")
    conditions: list[dict[str, Any]] = Field(default_factory=list, description="过滤条件")
    order_by: str = Field(default="-update_time", description="排序字段")
    scenario: list[str] | None = Field(default=None, description="场景过滤")
    with_user_group: bool = Field(default=True, description="是否返回用户组信息")
    with_user_group_detail: bool = Field(default=False, description="是否返回用户组详情")


class AlarmStrategySearchWithoutBiz(BaseModel):
    """查询全业务告警策略请求"""

    page: int = Field(default=1, description="页码")
    page_size: int = Field(default=10, description="每页数量")
    conditions: list[dict[str, Any]] = Field(default_factory=list, description="过滤条件")
    scenario: list[str] | None = Field(default=None, description="场景过滤")


class AlarmStrategySave(BaseModel):
    """保存告警策略请求"""

    bk_biz_id: int = Field(description="业务 ID")
    name: str = Field(description="策略名称")
    source: str = Field(default="bk_monitorv3", description="来源")
    scenario: Literal["os", "host_process", "service_module", "component", "uptimecheck", "apm", "kubernetes"] = Field(
        default="os", description="场景"
    )
    type: Literal["Monitor", "MultivariateAnomaly"] = Field(default="Monitor", description="策略类型")
    is_enabled: bool = Field(default=False, description="是否启用")
    labels: list[str] = Field(default_factory=list, description="标签")
    items: list[AlarmStrategyItem] = Field(description="策略配置项")
    detects: list[AlarmStrategyDetect] = Field(description="检测配置")
    actions: list[dict[str, Any]] = Field(default_factory=list, description="执行动作")
    notice: AlarmStrategyNotice = Field(description="通知配置")

    # 可选字段，用于更新
    id: int | None = Field(default=None, description="策略 ID（更新时需要）")


class AlarmStrategySwitch(BaseModel):
    """启停告警策略请求"""

    bk_biz_id: int = Field(description="业务 ID")
    ids: list[int] = Field(description="策略 ID 列表")
    is_enabled: bool = Field(description="是否启用")


class AlarmStrategySwitchByLabels(BaseModel):
    """按标签批量启停策略请求"""

    bk_biz_id: int = Field(description="业务 ID")
    labels: list[str] = Field(description="标签列表")
    action: Literal["on", "off"] = Field(description="操作类型")


class AlarmStrategyDelete(BaseModel):
    """删除告警策略请求"""

    bk_biz_id: int = Field(description="业务 ID")
    ids: list[int] = Field(description="策略 ID 列表")


# ============== 策略数据模型（响应） ==============


class AlarmStrategyData(BaseModel):
    """告警策略数据"""

    id: int = Field(description="策略 ID")
    bk_biz_id: int = Field(description="业务 ID")
    name: str = Field(description="策略名称")
    source: str = Field(description="来源")
    scenario: str = Field(description="场景")
    type: str = Field(description="策略类型")
    is_enabled: bool = Field(description="是否启用")
    labels: list[str] = Field(default_factory=list, description="标签")
    create_time: str = Field(description="创建时间")
    update_time: str = Field(description="更新时间")
    create_user: str = Field(description="创建人")
    update_user: str = Field(description="更新人")


# ============== 工厂类：简化策略配置创建 ==============


class AlarmStrategyFactory:
    """
    告警策略工厂类

    提供简便方法创建常用的策略配置

    Example:
        >>> config = AlarmStrategyFactory.cpu_usage_strategy(
        ...     bk_biz_id=2,
        ...     name="CPU 告警",
        ...     threshold=90,
        ... )
        >>> client.save(config)
    """

    @staticmethod
    def default_query_config(
        metric_id: str = "bk_monitor.system.cpu_summary.usage",
        result_table_id: str = "system.cpu_summary",
        metric_field: str = "usage",
        unit: str = "percent",
        agg_method: str = "AVG",
    ) -> AlarmStrategyQueryConfig:
        """创建默认查询配置"""
        return AlarmStrategyQueryConfig(
            metric_id=metric_id,
            result_table_id=result_table_id,
            metric_field=metric_field,
            unit=unit,
            agg_method=agg_method,  # type: ignore
        )

    @staticmethod
    def threshold_algorithm(
        threshold: int | float = 90,
        method: Literal["gt", "gte", "lt", "lte", "eq", "neq"] = "gte",
        level: int = 1,
    ) -> AlarmStrategyAlgorithm:
        """创建阈值告警算法"""
        return AlarmStrategyAlgorithm(
            type="Threshold",
            level=level,  # type: ignore
            config=[[{"method": method, "threshold": threshold}]],
        )

    @staticmethod
    def default_item(
        name: str = "CPU使用率",
        query_config: AlarmStrategyQueryConfig | None = None,
        algorithm: AlarmStrategyAlgorithm | None = None,
    ) -> AlarmStrategyItem:
        """创建默认策略配置项"""
        return AlarmStrategyItem(
            name=name,
            query_configs=[query_config or AlarmStrategyFactory.default_query_config()],
            algorithms=[algorithm or AlarmStrategyFactory.threshold_algorithm()],
        )

    @staticmethod
    def default_detect(level: int = 1, trigger_count: int = 3, check_window: int = 5) -> AlarmStrategyDetect:
        """创建默认检测配置"""
        return AlarmStrategyDetect(
            level=level,  # type: ignore
            trigger_config=AlarmStrategyTriggerConfig(count=trigger_count, check_window=check_window),
        )

    @staticmethod
    def default_notice(user_groups: list[int] | None = None) -> AlarmStrategyNotice:
        """创建默认通知配置"""
        return AlarmStrategyNotice(user_groups=user_groups or [])

    @classmethod
    def cpu_usage_strategy(
        cls,
        bk_biz_id: int,
        name: str,
        threshold: int | float = 90,
        is_enabled: bool = False,
        labels: list[str] | None = None,
        user_groups: list[int] | None = None,
    ) -> AlarmStrategySave:
        """
        创建 CPU 使用率告警策略

        Args:
            bk_biz_id: 业务 ID
            name: 策略名称
            threshold: CPU 使用率阈值 (百分比)
            is_enabled: 是否启用
            labels: 标签列表
            user_groups: 通知组 ID 列表
        """
        return AlarmStrategySave(
            bk_biz_id=bk_biz_id,
            name=name,
            scenario="os",
            is_enabled=is_enabled,
            labels=labels or ["test", "api_test"],
            items=[
                cls.default_item(
                    name="CPU使用率",
                    algorithm=cls.threshold_algorithm(threshold=threshold),
                )
            ],
            detects=[cls.default_detect()],
            notice=cls.default_notice(user_groups=user_groups),
        )

    @classmethod
    def memory_usage_strategy(
        cls,
        bk_biz_id: int,
        name: str,
        threshold: int | float = 80,
        is_enabled: bool = False,
        labels: list[str] | None = None,
        user_groups: list[int] | None = None,
    ) -> AlarmStrategySave:
        """
        创建内存使用率告警策略
        """
        return AlarmStrategySave(
            bk_biz_id=bk_biz_id,
            name=name,
            scenario="os",
            is_enabled=is_enabled,
            labels=labels or ["test", "api_test"],
            items=[
                cls.default_item(
                    name="内存使用率",
                    query_config=cls.default_query_config(
                        metric_id="bk_monitor.system.mem.pct_used",
                        result_table_id="system.mem",
                        metric_field="pct_used",
                        unit="percent",
                    ),
                    algorithm=cls.threshold_algorithm(threshold=threshold),
                )
            ],
            detects=[cls.default_detect()],
            notice=cls.default_notice(user_groups=user_groups),
        )
