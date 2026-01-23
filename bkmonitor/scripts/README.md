# BK-Resource URL 追踪工具

快速追踪 BK-Resource 框架中的 URL 到对应的代码位置。

## 使用方式

### 1. MCP 工具（推荐 - AI 集成）

配置完成后，直接对 AI 说：
```
"帮我追踪这个 URL: https://bkmonitor.bkop.woa.com/rest/v2/grafana/dashboards/"
```

### 2. 命令行

```bash
# URL 追踪
python3 scripts/trace_url_to_code.py \
  --url "https://bkmonitor.bkop.woa.com/rest/v2/grafana/dashboards/" \
  --method GET

# Resource 反向追踪
python3 scripts/trace_url_to_code.py \
  --resource "apm.create_application"

# 交互式模式
python3 scripts/trace_url_to_code.py
```

## 支持的 URL 格式

- ✅ 完整 URL: `https://bkmonitor.bkop.woa.com/rest/v2/grafana/dashboards/`
- ✅ 路径: `/rest/v2/grafana/dashboards/`
- ✅ 简短路径: `/grafana/dashboards/`
- ✅ 带查询参数: `?bk_biz_id=2`

## MCP Server

MCP Server 位于: `.codebuddy/mcp-server/bk-resource-tracer/`

Codebuddy 会自动加载并提供以下工具：
- `trace_url` - URL 追踪
- `trace_resource` - Resource 反向追踪
