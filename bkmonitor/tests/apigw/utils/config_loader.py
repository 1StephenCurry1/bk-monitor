"""
配置加载器

支持按环境目录加载配置，环境从 config/ 目录下动态发现。
每个包含 settings.yaml 的子目录即为一个有效环境。

通过环境变量 APIGW_TEST_ENV 指定当前环境
"""

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


# 默认环境（当环境变量未设置时使用）
DEFAULT_ENVIRONMENT: str = "paas3"

# 环境变量名
ENV_VAR_NAME = "APIGW_TEST_ENV"

# 配置基础目录
CONFIG_BASE_DIR = Path(__file__).parent.parent / "config"


@lru_cache(maxsize=1)
def discover_environments() -> tuple[str, ...]:
    """
    从 config/ 目录动态发现可用环境

    规则：包含 settings.yaml 文件的子目录即为有效环境

    Returns:
        可用环境名称元组
    """
    if not CONFIG_BASE_DIR.exists():
        return ()

    environments = []
    for item in CONFIG_BASE_DIR.iterdir():
        if item.is_dir() and (item / "settings.yaml").exists():
            environments.append(item.name)

    return tuple(sorted(environments))


def get_valid_environments() -> tuple[str, ...]:
    """获取所有有效环境名称"""
    return discover_environments()


class ApiConfig(BaseModel):
    """API 配置"""

    base_url: str = Field(description="API 网关基础 URL")
    timeout: int = Field(default=30, description="请求超时时间（秒）")
    retry_count: int = Field(default=3, description="重试次数")
    retry_interval: float = Field(default=1.0, description="重试间隔（秒）")


class AuthConfig(BaseModel):
    """认证配置（使用 app_code + app_secret）"""

    app_code: str = Field(default="", description="App Code")
    app_secret: str = Field(default="", description="App Secret")

    @field_validator("app_code", "app_secret", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> str:
        """将 None 转换为空字符串"""
        return v if v is not None else ""


class BizConfig(BaseModel):
    """业务配置"""

    bk_biz_id: int = Field(default=2, description="测试业务 ID")


class LoggingConfig(BaseModel):
    """日志配置"""

    level: str = Field(default="INFO", description="日志级别")
    verbose: bool = Field(default=False, description="是否打印请求响应详情")


class Settings(BaseModel):
    """全局配置"""

    environment: str = Field(default="paas3", description="环境名称（op/paas3/prod）")
    config_dir: Path = Field(description="当前环境配置目录路径")
    api: ApiConfig
    auth: AuthConfig = Field(default_factory=AuthConfig)
    biz: BizConfig = Field(default_factory=BizConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    model_config = {"arbitrary_types_allowed": True}

    @property
    def api_base_url(self) -> str:
        """获取 API 基础 URL"""
        return self.api.base_url.rstrip("/")

    @property
    def test_data_dir(self) -> Path:
        """获取测试数据目录路径"""
        return self.config_dir / "test_data"


def _substitute_env_vars(value: Any) -> Any:
    """
    递归替换配置值中的环境变量

    支持格式：
    - ${ENV_VAR} - 必须的环境变量
    - ${ENV_VAR:default} - 带默认值的环境变量
    """
    if isinstance(value, str):
        # 匹配 ${VAR} 或 ${VAR:default}
        pattern = r"\$\{([^}:]+)(?::([^}]*))?\}"

        def replacer(match: re.Match[str]) -> str:
            env_var = match.group(1)
            default = match.group(2)
            env_value = os.environ.get(env_var)
            if env_value is not None:
                return env_value
            if default is not None:
                return default
            # 如果没有默认值且环境变量不存在，返回空字符串
            return ""

        return re.sub(pattern, replacer, value)
    elif isinstance(value, dict):
        return {k: _substitute_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_substitute_env_vars(item) for item in value]
    return value


def get_current_environment() -> str:
    """
    获取当前环境名称

    优先级：
    1. 环境变量 APIGW_TEST_ENV
    2. 默认值 paas3
    """
    env = os.environ.get(ENV_VAR_NAME, DEFAULT_ENVIRONMENT)
    valid_envs = get_valid_environments()

    if env not in valid_envs:
        raise ValueError(f"无效的环境名称: {env}，支持的环境: {', '.join(valid_envs)}")
    return env


def get_config_dir(environment: str | None = None) -> Path:
    """
    获取指定环境的配置目录路径

    Args:
        environment: 环境名称，为 None 时从环境变量获取

    Returns:
        配置目录路径
    """
    if environment is None:
        environment = get_current_environment()

    valid_envs = get_valid_environments()
    if environment not in valid_envs:
        raise ValueError(f"无效的环境名称: {environment}，支持的环境: {', '.join(valid_envs)}")

    config_dir = CONFIG_BASE_DIR / environment

    if not config_dir.exists():
        raise FileNotFoundError(f"环境配置目录不存在: {config_dir}")

    return config_dir


def load_settings(environment: str | None = None) -> Settings:
    """
    加载指定环境的配置

    Args:
        environment: 环境名称（op/paas3/prod），为 None 时从环境变量获取

    Returns:
        Settings 配置对象
    """
    if environment is None:
        environment = get_current_environment()

    config_dir = get_config_dir(environment)
    config_path = config_dir / "settings.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)

    if raw_config is None:
        raw_config = {}

    # 替换环境变量
    config = _substitute_env_vars(raw_config)

    # 构建 Settings 对象
    settings_dict = {
        "environment": environment,
        "config_dir": config_dir,
        "api": config.get("api", {}),
        "auth": config.get("auth", {}),
        "biz": config.get("biz", {}),
        "logging": config.get("logging", {}),
    }

    return Settings.model_validate(settings_dict)


def load_test_data(filename: str, environment: str | None = None) -> dict[str, Any]:
    """
    加载指定环境的测试数据文件

    Args:
        filename: 测试数据文件名（如 uptime_check.yaml）
        environment: 环境名称，为 None 时从环境变量获取

    Returns:
        测试数据字典
    """
    if environment is None:
        environment = get_current_environment()

    config_dir = get_config_dir(environment)
    data_path = config_dir / "test_data" / filename

    if not data_path.exists():
        raise FileNotFoundError(f"测试数据文件不存在: {data_path}")

    with open(data_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data or {}


# 全局配置实例（延迟加载）
_settings: Settings | None = None


def get_settings() -> Settings:
    """获取全局配置实例（单例模式）"""
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def reload_settings(environment: str | None = None) -> Settings:
    """
    重新加载配置

    Args:
        environment: 环境名称（op/paas3/prod）
    """
    global _settings
    _settings = load_settings(environment=environment)
    return _settings
