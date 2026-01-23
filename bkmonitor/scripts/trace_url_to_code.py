#!/usr/bin/env python
"""
BK-Monitor URL 追踪工具
从 URL 追踪到对应的 ViewSet/Resource/Serializer 代码位置
"""

import sys
import re
import argparse
from pathlib import Path
from urllib.parse import urlparse, parse_qs

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def parse_url(url: str) -> tuple[str, str, list[str], dict]:
    """解析 URL，提取模块名、端点、路径部分和查询参数"""
    query_params = {}
    if url.startswith("http://") or url.startswith("https://"):
        parsed = urlparse(url)
        url = parsed.path
        query_params = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(parsed.query).items()}
    elif "?" in url:
        url, query_string = url.split("?", 1)
        query_params = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(query_string).items()}

    url = url.strip("/")
    parts = [p for p in url.split("/") if p]

    # 移除常见前缀
    while parts and parts[0] in ["rest", "api", "v1", "v2", "v3", "v4"]:
        parts.pop(0)

    if not parts:
        raise ValueError(f"URL 解析失败: {url}")

    module_name = parts[0]
    endpoint = parts[-1] if len(parts) > 1 else ""

    return module_name, endpoint, parts, query_params


def find_endpoint_in_views(module_name: str, endpoint: str, url_parts: list[str] = None) -> list[dict]:
    """在 views.py 中查找端点，支持 ResourceRoute 和 @action 装饰器"""
    results = []
    search_dirs = [
        PROJECT_ROOT / "packages" / "monitor_web" / module_name,
        PROJECT_ROOT / "packages" / "apm_web" / module_name,
        PROJECT_ROOT / "kernel_api" / "views",
        PROJECT_ROOT / module_name,
    ]

    # 从 URL 提取可能的 ViewSet 名称 (uptime_check_task -> UptimeCheckTaskViewSet)
    viewset_hint = None
    if url_parts and len(url_parts) > 1:
        viewset_hint = "".join(word.capitalize() for word in url_parts[-2].split("_")) + "ViewSet"

    for base_dir in search_dirs:
        if not base_dir.exists():
            continue

        for py_file in base_dir.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                lines = content.split("\n")

                current_viewset = None
                action_decorator_line = None

                for i, line in enumerate(lines, 1):
                    # 跟踪当前所在的 ViewSet 类
                    class_match = re.search(r"class\s+(\w+ViewSet)", line)
                    if class_match:
                        current_viewset = class_match.group(1)

                    # 查找 @action 装饰器
                    if "@action" in line:
                        action_decorator_line = i

                    # 查找 def {endpoint} 方法（@action 对应的方法）
                    method_def_match = re.search(rf"def\s+{re.escape(endpoint)}\s*\(", line)
                    if method_def_match:
                        # 检查是否是 @action 装饰器的方法
                        if action_decorator_line and i - action_decorator_line <= 2:
                            # 提取 @action 的 methods 参数
                            decorator_line = lines[action_decorator_line - 1]
                            methods_match = re.search(r"methods=\[([^\]]+)\]", decorator_line)
                            methods = methods_match.group(1) if methods_match else "GET"

                            results.append(
                                {
                                    "type": "@action",
                                    "file": str(py_file.relative_to(PROJECT_ROOT)),
                                    "line": i,
                                    "code": line.strip(),
                                    "viewset": current_viewset,
                                    "methods": methods.replace('"', "").replace("'", ""),
                                    "decorator_line": action_decorator_line,
                                }
                            )
                        action_decorator_line = None

                    # 查找 ResourceRoute 定义
                    if endpoint in line and "ResourceRoute" in line:
                        resource_match = re.search(r"resource\.(\w+)\.(\w+)", line)
                        method_match = re.search(r'["\'](\w+)["\']', line)

                        results.append(
                            {
                                "type": "ResourceRoute",
                                "file": str(py_file.relative_to(PROJECT_ROOT)),
                                "line": i,
                                "code": line.strip(),
                                "resource": f"{resource_match.group(1)}.{resource_match.group(2)}"
                                if resource_match
                                else None,
                                "method": method_match.group(1) if method_match else None,
                                "viewset": current_viewset,
                            }
                        )

                    # 查找 endpoint= 定义
                    if f'endpoint="{endpoint}"' in line or f"endpoint='{endpoint}'" in line:
                        results.append(
                            {
                                "type": "endpoint",
                                "file": str(py_file.relative_to(PROJECT_ROOT)),
                                "line": i,
                                "code": line.strip(),
                                "viewset": current_viewset,
                            }
                        )

            except Exception:
                continue

    # 按优先级排序，ViewSet 名称匹配的结果优先
    results.sort(key=lambda match: 0 if (viewset_hint and match.get("viewset") == viewset_hint) else 1)
    return results


def find_resource_class(resource_path: str) -> list[dict]:
    """查找 Resource 类定义"""
    results = []

    if "." in resource_path:
        _, resource_name = resource_path.rsplit(".", 1)
    else:
        resource_name = resource_path

    # 转换为类名格式 (get_directory_tree -> GetDirectoryTree)
    class_name = "".join(word.capitalize() for word in resource_name.split("_"))
    class_name_resource = class_name + "Resource"

    search_dirs = [
        PROJECT_ROOT / "packages" / "monitor_web",
        PROJECT_ROOT / "packages" / "apm_web",
        PROJECT_ROOT / "kernel_api",
    ]

    for base_dir in search_dirs:
        if not base_dir.exists():
            continue

        for py_file in base_dir.rglob("*.py"):
            if "resource" not in py_file.name and "resource" not in str(py_file.parent):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                lines = content.split("\n")

                for i, line in enumerate(lines, 1):
                    if f"class {class_name}" in line or f"class {class_name_resource}" in line:
                        # 获取类的简要信息
                        docstring = ""
                        if i < len(lines) and '"""' in lines[i]:
                            docstring = lines[i].strip().replace('"""', "")

                        results.append(
                            {
                                "type": "Resource",
                                "class_name": class_name if f"class {class_name}" in line else class_name_resource,
                                "file": str(py_file.relative_to(PROJECT_ROOT)),
                                "line": i,
                                "docstring": docstring,
                            }
                        )
            except Exception:
                continue

    return results


def trace_url(url: str, method: str = "GET") -> dict:
    """追踪 URL 到代码位置"""
    result = {
        "url": url,
        "method": method,
        "module": None,
        "endpoint": None,
        "url_parts": [],
        "query_params": {},
        "viewset_matches": [],
        "resource_matches": [],
        "urls_file": None,
    }

    try:
        module_name, endpoint, url_parts, query_params = parse_url(url)
        result["module"] = module_name
        result["endpoint"] = endpoint
        result["url_parts"] = url_parts
        result["query_params"] = query_params
    except Exception as e:
        result["error"] = str(e)
        return result

    # 查找 urls.py
    urls_paths = [
        PROJECT_ROOT / "packages" / "monitor_web" / module_name / "urls.py",
        PROJECT_ROOT / "packages" / "apm_web" / module_name / "urls.py",
        PROJECT_ROOT / module_name / "urls.py",
    ]
    for p in urls_paths:
        if p.exists():
            result["urls_file"] = str(p.relative_to(PROJECT_ROOT))
            break

    # 查找 ViewSet/endpoint
    result["viewset_matches"] = find_endpoint_in_views(module_name, endpoint, url_parts)

    # 查找 Resource 类
    for match in result["viewset_matches"]:
        if match.get("resource"):
            resource_matches = find_resource_class(match["resource"])
            result["resource_matches"].extend(resource_matches)

    return result


def format_file_location(file_path: str, line: int, end_line: int = None) -> str:
    """格式化文件位置，使用 IDE 兼容的格式"""
    if end_line and end_line != line:
        return f"文件：{file_path} (第 {line}-{end_line} 行)"
    return f"文件：{file_path} (第 {line} 行)"


def format_output(result: dict) -> str:
    """格式化输出结果"""
    lines = []
    lines.append("=" * 80)
    lines.append(f"🔍 追踪 URL: {result['url']}")
    lines.append(f"📋 方法: {result['method']}")
    lines.append("=" * 80)
    lines.append("")

    if result.get("error"):
        lines.append(f"❌ 错误: {result['error']}")
        return "\n".join(lines)

    lines.append(f"📦 模块: {result['module']}")
    lines.append(f"🎯 端点: {result['endpoint']}")
    if result.get("url_parts"):
        lines.append(f"📂 路径: {' / '.join(result['url_parts'])}")
    if result["query_params"]:
        lines.append(f"🔗 参数: {result['query_params']}")
    lines.append("")

    if result["urls_file"]:
        lines.append(f"✅ URLs 配置：{result['urls_file']}")

    if result["viewset_matches"]:
        lines.append("")
        lines.append("📍 代码定位:")
        for match in result["viewset_matches"]:
            match_type = match.get("type", "unknown")
            file_loc = format_file_location(match["file"], match["line"])

            if match_type == "@action":
                lines.append(f"   • [{match_type}] {file_loc}")
                if match.get("viewset"):
                    lines.append(f"     ViewSet: {match['viewset']}")
                lines.append(f"     Methods: {match.get('methods', 'GET')}")
                lines.append(f"     {match['code']}")
            elif match_type == "ResourceRoute":
                lines.append(f"   • [{match_type}] {file_loc}")
                if match.get("viewset"):
                    lines.append(f"     ViewSet: {match['viewset']}")
                lines.append(f"     {match['code'][:100]}...")
                if match.get("resource"):
                    lines.append(f"     → Resource: {match['resource']}")
            else:
                lines.append(f"   • [{match_type}] {file_loc}")
                lines.append(f"     {match['code'][:100]}...")

    if result["resource_matches"]:
        lines.append("")
        lines.append("📍 Resource 类:")
        for match in result["resource_matches"]:
            file_loc = format_file_location(match["file"], match["line"])
            lines.append(f"   • {match['class_name']}")
            lines.append(f"     {file_loc}")
            if match.get("docstring"):
                lines.append(f'     "{match["docstring"]}"')

    if not result["viewset_matches"] and not result["resource_matches"]:
        lines.append("")
        lines.append("⚠️  未找到精确匹配，建议手动搜索:")
        lines.append(f"   grep -r '{result['endpoint']}' packages/monitor_web/{result['module']}/")

    lines.append("")
    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="BK-Monitor URL 追踪工具")
    parser.add_argument("--url", help="要追踪的 URL")
    parser.add_argument("--method", default="GET", help="HTTP 方法")
    parser.add_argument("--resource", help="反向追踪 Resource")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")

    args = parser.parse_args()

    if args.url:
        result = trace_url(args.url, args.method)
        if args.json:
            import json

            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_output(result))

    elif args.resource:
        matches = find_resource_class(args.resource)
        print(f"\n🔍 查找 Resource: {args.resource}")
        print("=" * 60)
        if matches:
            for match in matches:
                print(f"✅ {match['class_name']}")
                print(f"   文件：{match['file']} (第 {match['line']} 行)")
        else:
            print("❌ 未找到匹配的 Resource")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
