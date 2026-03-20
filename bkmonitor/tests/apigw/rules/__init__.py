"""
API 响应校验规则集合

各模块的校验规则统一从此处导出，便于使用：

    from tests.apigw.rules import UptimeCheckRules
    from tests.apigw.rules import AlarmStrategyRules

或者按模块导入：

    from tests.apigw.rules.uptime_check import UptimeCheckRules
    from tests.apigw.rules.alarm_strategy import AlarmStrategyRules
"""

from tests.apigw.rules.alarm_strategy import AlarmStrategyRules
from tests.apigw.rules.uptime_check import UptimeCheckRules

__all__ = [
    "AlarmStrategyRules",
    "UptimeCheckRules",
]
