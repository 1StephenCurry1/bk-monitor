#!/usr/bin/env python
"""
APIGW 自动化测试运行脚本

支持通过 --env 参数指定测试环境：
    ./run_tests.py --env paas3
    ./run_tests.py --env op
    ./run_tests.py --env prod

支持传递 pytest 参数：
    ./run_tests.py --env paas3 -v --tb=short
    ./run_tests.py --env paas3 -k "test_group"

支持指定测试模块或文件（路径相对于 apigw 目录或 tests 目录）：
    ./run_tests.py --env paas3 tests/test_uptime_check/
    ./run_tests.py --env paas3 test_uptime_check/test_group_crud.py
    ./run_tests.py --env paas3 tests/test_alert/

默认环境为 paas3，默认运行 tests/ 下所有测试
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# 将当前目录加入路径以便导入 utils（绕过 __init__.py 中的导入）
_apigw_dir = Path(__file__).parent
sys.path.insert(0, str(_apigw_dir))

# 直接导入 config_loader 模块，避免触发 utils/__init__.py
import importlib.util

_loader_spec = importlib.util.spec_from_file_location("config_loader", _apigw_dir / "utils" / "config_loader.py")
_config_loader = importlib.util.module_from_spec(_loader_spec)
_loader_spec.loader.exec_module(_config_loader)

DEFAULT_ENVIRONMENT = _config_loader.DEFAULT_ENVIRONMENT
ENV_VAR_NAME = _config_loader.ENV_VAR_NAME
get_valid_environments = _config_loader.get_valid_environments


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    """
    解析命令行参数

    Returns:
        (args, pytest_args): 解析后的参数对象和传递给 pytest 的参数
    """
    valid_envs = get_valid_environments()

    parser = argparse.ArgumentParser(
        description="APIGW 自动化测试运行脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
示例:
    %(prog)s --env paas3                              # 运行所有测试
    %(prog)s --env paas3 -v                           # 详细输出
    %(prog)s --env paas3 -k "test_group"              # 按关键字筛选
    %(prog)s --env paas3 tests/test_uptime_check/     # 运行指定模块
    %(prog)s --env paas3 test_uptime_check/           # 相对于 tests 目录
    %(prog)s --env paas3 test_alert/ test_metric/     # 运行多个模块
    %(prog)s --list-env                               # 列出所有可用环境

可用环境: {", ".join(valid_envs)}
        """,
    )

    parser.add_argument(
        "--env",
        choices=valid_envs,
        default=DEFAULT_ENVIRONMENT,
        help=f"测试环境 (默认: {DEFAULT_ENVIRONMENT})",
    )

    parser.add_argument(
        "--list-env",
        action="store_true",
        help="列出所有可用环境及其配置",
    )

    # 解析已知参数，剩余的传递给 pytest
    args, pytest_args = parser.parse_known_args()

    return args, pytest_args


def list_environments() -> None:
    """列出所有可用环境及其配置"""
    import yaml

    config_base = Path(__file__).parent / "config"
    valid_envs = get_valid_environments()

    print("\n可用的测试环境:")
    print("=" * 60)

    for env in valid_envs:
        env_dir = config_base / env
        settings_file = env_dir / "settings.yaml"

        print(f"\n【{env}】")

        if not env_dir.exists():
            print(f"  ⚠️  配置目录不存在: {env_dir}")
            continue

        if not settings_file.exists():
            print(f"  ⚠️  配置文件不存在: {settings_file}")
            continue

        try:
            with open(settings_file, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            api_url = config.get("api", {}).get("base_url", "未配置")
            biz_id = config.get("biz", {}).get("bk_biz_id", "未配置")

            print(f"  API URL:    {api_url}")
            print(f"  bk_biz_id:  {biz_id}")

            # 检查测试数据
            test_data_dir = env_dir / "test_data"
            if test_data_dir.exists():
                data_files = list(test_data_dir.glob("*.yaml"))
                print(f"  测试数据:   {len(data_files)} 个文件")
            else:
                print("  测试数据:   ⚠️  目录不存在")

        except Exception as e:
            print(f"  ❌ 读取配置失败: {e}")

    print("\n" + "=" * 60)
    print(f"默认环境: {DEFAULT_ENVIRONMENT}")
    print("使用方式: ./run_tests.py --env <环境名>")
    print()


def run_tests(environment: str, pytest_args: list[str]) -> int:
    """
    运行测试

    Args:
        environment: 环境名称
        pytest_args: 传递给 pytest 的参数

    Returns:
        pytest 退出码
    """
    # 设置环境变量
    os.environ[ENV_VAR_NAME] = environment

    # 获取目录
    apigw_dir = Path(__file__).parent
    tests_dir = apigw_dir / "tests"

    # 处理 pytest_args，转换相对路径为绝对路径
    processed_args = []
    has_test_path = False  # 是否指定了测试路径（-k 等过滤器不算）

    i = 0
    while i < len(pytest_args):
        arg = pytest_args[i]

        # 检查是否是需要跳过下一个参数的选项（如 -k, -m, --ignore 等）
        if arg in ("-k", "-m", "--ignore", "--ignore-glob", "-p", "--co", "--collect-only"):
            processed_args.append(arg)
            if i + 1 < len(pytest_args):
                i += 1
                processed_args.append(pytest_args[i])
            i += 1
            continue

        # 检查是否是 -k=xxx 或 --keyword=xxx 形式
        if arg.startswith("-k=") or arg.startswith("--keyword="):
            processed_args.append(arg)
            i += 1
            continue

        # 非选项参数，可能是测试路径
        if not arg.startswith("-"):
            # 尝试多个可能的路径
            potential_paths = [
                Path(arg),  # 绝对路径或当前目录相对路径
                apigw_dir / arg,  # 相对于 apigw 目录
                tests_dir / arg,  # 相对于 tests 目录
            ]

            resolved = False
            for path in potential_paths:
                if path.exists():
                    processed_args.append(str(path.resolve()))
                    has_test_path = True
                    resolved = True
                    break

            if not resolved:
                # 可能是 pytest 的其他位置参数（如 node id），保持原样
                processed_args.append(arg)
                # 如果包含 :: 说明是 pytest node id，视为有测试路径
                if "::" in arg:
                    has_test_path = True

            i += 1
            continue

        # 其他选项，直接添加
        processed_args.append(arg)
        i += 1

    # 构建 pytest 命令
    cmd = [sys.executable, "-m", "pytest"]

    # 如果没有指定测试路径，默认运行整个 tests 目录
    if not has_test_path:
        cmd.append(str(tests_dir))

    cmd.extend(processed_args)

    # 打印运行信息
    print(f"\n{'=' * 60}")
    print("🚀 APIGW 自动化测试")
    print("=" * 60)
    print(f"环境: {environment}")
    print(f"命令: {' '.join(cmd)}")
    print("=" * 60 + "\n")

    # 运行 pytest，工作目录设为 bkmonitor
    result = subprocess.run(cmd, cwd=apigw_dir.parent)

    return result.returncode


def main() -> int:
    """主入口函数"""
    args, pytest_args = parse_args()

    # 列出环境
    if args.list_env:
        list_environments()
        return 0

    # 运行测试
    return run_tests(args.env, pytest_args)


if __name__ == "__main__":
    sys.exit(main())
