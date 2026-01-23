# 导出JSON文件格式说明

## 文件整体结构

导出的JSON文件采用以下顶层结构：

```json
{
  "version": "1.0",
  "export_time": 1737446400,
  "source_env": "production",
  "resources": {
    "action_plugin": [...],
    "user_group": [...],
    "strategy": [...],
    ...
  },
  "metadata": {
    "id_mapping": {...},
    "adapters_applied": [...]
  }
}
```

## 顶层字段说明

### 1. `version` (字符串)
- **作用**: 标识导出文件的格式版本
- **当前值**: `"1.0"`
- **用途**: 用于兼容性检查，确保导入器能正确解析文件格式

### 2. `export_time` (整数)
- **作用**: 记录导出时间
- **格式**: Unix时间戳（秒）
- **示例**: `1737446400` (对应 2026-01-21 00:00:00)
- **用途**: 
  - 追溯数据导出时间
  - 用于文件命名（`monitor_config_export_20260121_120000.json`）
  - 审计和版本管理

### 3. `source_env` (字符串)
- **作用**: 标识数据来源环境
- **可能值**: `"production"`, `"staging"`, `"development"`, `"unknown"`
- **来源**: 从环境变量 `BKAPP_DEPLOY_ENV` 读取
- **用途**: 
  - 区分不同环境的数据
  - 防止误操作（如将生产数据导入测试环境）

### 4. `resources` (对象)
- **作用**: 存储所有导出的资源数据
- **结构**: 键值对，键为资源类型，值为该类型的对象数组
- **示例**:
  ```json
  {
    "action_plugin": [对象1, 对象2, ...],
    "strategy": [对象1, 对象2, ...],
    ...
  }
  ```

### 5. `metadata` (对象)
- **作用**: 存储导出过程的元数据
- **包含字段**:
  - `id_mapping`: ID映射表（记录所有导出对象的原始ID）
  - `adapters_applied`: 应用的适配器列表

---

## `resources` 字段详解

### 资源类型列表

按照依赖关系排序（导出/导入顺序）：

```python
EXPORT_ORDER = [
    "action_plugin",      # 响应动作插件（内置插件）
    "collector_plugin",   # 采集插件
    "duty_rule",          # 轮值规则
    "user_group",         # 告警组
    "action_config",      # 处理套餐
    "custom_ts_group",    # 自定义时序分组
    "custom_ts_table",    # 自定义时序表
    "collect_config",     # 采集配置
    "strategy",           # 告警策略
    "shield",             # 告警屏蔽
    "alert_assign_group", # 告警分派
    "dashboard",          # 仪表盘
]
```

### 单个资源对象的通用结构

每个资源对象都包含以下部分：

```json
{
  // 1. 模型字段（来自Django Model）
  "id": 123,
  "name": "示例策略",
  "bk_biz_id": 2,
  "create_time": 1737446400,
  "update_time": 1737446400,
  "creator": "admin",
  "updater": "admin",
  // ... 其他模型字段
  
  // 2. 外键字段（存储ID而非对象）
  "user_group_id": 456,
  "action_config_id": 789,
  
  // 3. 关联数据（可选，存储在 _relations 中）
  "_relations": {
    "items": [...],      // 一对多关联
    "detects": [...],    // 一对多关联
    "algorithms": [...]  // 一对多关联
  },
  
  // 4. 元数据（必需）
  "_metadata": {
    "resource_type": "strategy",
    "original_id": 123
  }
}
```

---

## 字段类型说明

### 1. **模型字段**
- **来源**: Django Model 的所有字段
- **处理规则**:
  - 普通字段：直接序列化
  - 外键字段：只保存ID（如 `user_group_id: 456`）
  - JSONField：保持JSON格式
  - DateTimeField：转换为Unix时间戳（整数）
  - DecimalField：转换为浮点数
  - None值：保持为 `null`

### 2. **`_relations` 字段**（可选）
- **作用**: 存储一对多或多对多的关联对象
- **命名规则**: 使用关联字段的复数形式（如 `items`, `detects`）
- **数据格式**: 数组，每个元素是关联对象的完整数据
- **示例**:
  ```json
  "_relations": {
    "items": [
      {
        "id": 1,
        "strategy_id": 123,
        "name": "CPU使用率",
        "metric_id": "system.cpu.usage",
        ...
      },
      {
        "id": 2,
        "strategy_id": 123,
        "name": "内存使用率",
        ...
      }
    ],
    "detects": [...],
    "algorithms": [...]
  }
  ```

### 3. **`_metadata` 字段**（必需）
- **作用**: 存储对象的元数据，用于导入时识别和处理
- **字段说明**:
  - `resource_type`: 资源类型标识（如 `"strategy"`, `"user_group"`）
  - `original_id`: 原始主键ID（用于ID映射和冲突检查）

---

## 特殊资源的数据结构

### 1. **Strategy（告警策略）**

```json
{
  "id": 123,
  "name": "CPU使用率告警",
  "bk_biz_id": 2,
  "scenario": "os",
  "is_enabled": true,
  "user_groups": [1, 2, 3],  // JSONField，存储告警组ID列表
  "action_config_id": 456,
  "create_time": 1737446400,
  
  "_relations": {
    "items": [
      {
        "id": 1,
        "strategy_id": 123,
        "name": "CPU使用率",
        "metric_id": "system.cpu.usage",
        "data_source_label": "bk_monitor",
        "data_type_label": "time_series"
      }
    ],
    "detects": [
      {
        "id": 1,
        "strategy_id": 123,
        "level": 1,
        "expression": "",
        "trigger_config": {...},
        "recovery_config": {...}
      }
    ],
    "algorithms": [
      {
        "id": 1,
        "strategy_id": 123,
        "type": "Threshold",
        "level": 1,
        "config": [[{"method": "gte", "threshold": 90}]]
      }
    ]
  },
  
  "_metadata": {
    "resource_type": "strategy",
    "original_id": 123
  }
}
```

### 2. **UserGroup（告警组）**

```json
{
  "id": 456,
  "name": "运维组",
  "bk_biz_id": 2,
  "desc": "负责基础设施监控",
  "duty_rules": [10, 11, 12],  // JSONField，存储轮值规则ID列表
  "alert_notice": [...],
  "action_notice": [...],
  
  "_relations": {
    "duty_arranges": [
      {
        "id": 1,
        "user_group_id": 456,
        "duty_type": "daily",
        "work_time": "00:00--23:59",
        "users": [...]
      }
    ],
    "duty_rules": [
      {
        "id": 10,
        "name": "工作日轮值",
        "bk_biz_id": 2,
        "effective_time": "2026-01-01 00:00:00",
        "end_time": "2026-12-31 23:59:59",
        "category": "regular"
      }
    ]
  },
  
  "_metadata": {
    "resource_type": "user_group",
    "original_id": 456
  }
}
```

### 3. **CustomTSTable（自定义时序表）**

```json
{
  "time_series_group_id": 100,  // 主键（不是id）
  "name": "自定义指标表",
  "bk_biz_id": 2,
  "table_id": "custom_metrics_100",
  "is_enable": true,
  
  "_relations": {
    "fields": [
      {
        "id": 1,
        "time_series_group_id": 100,
        "name": "cpu_usage",
        "type": "float",
        "unit": "%",
        "description": "CPU使用率"
      },
      {
        "id": 2,
        "time_series_group_id": 100,
        "name": "memory_usage",
        "type": "float",
        "unit": "%"
      }
    ]
  },
  
  "_metadata": {
    "resource_type": "custom_ts_table",
    "original_id": 100
  }
}
```

### 4. **CollectConfig（采集配置）**

```json
{
  "id": 789,
  "name": "Nginx日志采集",
  "bk_biz_id": 2,
  "collect_type": "log",
  "target_object_type": "HOST",
  "deployment_config_id": 999,  // 外键
  "plugin_id": "nginx_log",
  
  "_relations": {
    "deployment_config": {
      "id": 999,
      "config_meta_id": 789,
      "plugin_version_id": 888,
      "params": {...},
      "target_nodes": [...],
      
      "_plugin_version": {
        "id": 888,
        "plugin_id": "nginx_log",
        "config_version": 1,
        "info_version": 1,
        
        "_config": {
          "id": 777,
          "plugin_id": "nginx_log",
          "config_json": [...]
        },
        "_info": {
          "id": 666,
          "plugin_id": "nginx_log",
          "plugin_display_name": "Nginx日志采集",
          "description": "..."
        }
      }
    },
    "plugin": {
      "plugin_id": "nginx_log",
      "plugin_type": "Log",
      "bk_tenant_id": 1
    }
  },
  
  "_metadata": {
    "resource_type": "collect_config",
    "original_id": 789
  }
}
```

---

## `metadata` 字段详解

### 1. `export_summary` 结构

```json
{
  "export_summary": {
    "strategy": 234,
    "user_group": 12,
    "duty_rule": 3,
    "action_plugin": 7,
    "collector_plugin": 45
  }
}
```

**说明**:
- **键**: 资源类型
- **值**: 导出的对象数量（整数）
- **用途**: 
  - 统计导出的资源数量
  - 审计和验证
  - 快速了解导出内容

### 2. `adapters_applied` 结构

```json
{
  "adapters_applied": [
    "biz_id_mapping",
    "user_mapping",
    "domain_mapping",
    "sensitive_fields_config"
  ]
}
```

**说明**:
- **类型**: 字符串数组
- **内容**: 导出时应用的适配器名称列表
- **用途**: 
  - 记录数据转换历史
  - 导入时可以反向应用适配器
  - 审计和调试

---

### 已移除的字段

#### `id_mapping`（已弃用）

在旧版本中，`metadata` 包含 `id_mapping` 字段：

```json
{
  "id_mapping": {
    "strategy": {"123": null, "124": null},
    "user_group": {"456": null}
  }
}
```

**为什么移除**：
- 在全量迁移模式下，ID 保持不变，不需要映射
- 该字段从未被实际使用（`get_new_id()` 方法从未被调用）
- 增加了 JSON 文件大小，但没有实际价值

**向后兼容性**：
- 导入器会忽略旧格式文件中的 `id_mapping` 字段
- 新格式文件不再包含此字段

---

## 数据处理规则

### 1. **DateTime 转换**
- **原始类型**: Python `datetime` 对象
- **导出格式**: Unix时间戳（整数，秒）
- **示例**: `datetime(2026, 1, 21, 12, 0, 0)` → `1737446400`

### 2. **Decimal 转换**
- **原始类型**: Python `Decimal` 对象
- **导出格式**: 浮点数
- **示例**: `Decimal('99.99')` → `99.99`

### 3. **外键处理**
- **原始类型**: Django 外键对象
- **导出格式**: 整数ID
- **示例**: `strategy.user_group` (对象) → `strategy.user_group_id: 456`

### 4. **JSONField 处理**
- **原始类型**: JSON数据（dict/list）
- **导出格式**: 保持JSON格式
- **递归处理**: 内部的 datetime 和 decimal 也会被转换

### 5. **None 值处理**
- **原始类型**: Python `None`
- **导出格式**: JSON `null`

---

## 导出顺序的重要性

资源按照依赖关系排序导出，确保：

1. **基础资源优先**: 无依赖的资源先导出（如 `action_plugin`, `duty_rule`）
2. **依赖资源后导出**: 有外键依赖的资源后导出（如 `strategy` 依赖 `user_group`）
3. **导入时按相同顺序**: 确保外键引用的对象已存在

**依赖关系图**:
```
action_plugin (无依赖)
    ↓
action_config (依赖 action_plugin)
    ↓
user_group (依赖 duty_rule)
    ↓
strategy (依赖 user_group, action_config)
    ↓
shield (依赖 strategy)
```

---

## 完整示例

```json
{
  "version": "1.0",
  "export_time": 1737446400,
  "source_env": "production",
  "resources": {
    "action_plugin": [
      {
        "id": 1,
        "plugin_type": "notice",
        "name": "通知",
        "is_builtin": true,
        "_metadata": {
          "resource_type": "action_plugin",
          "original_id": 1
        }
      }
    ],
    "user_group": [
      {
        "id": 456,
        "name": "运维组",
        "bk_biz_id": 2,
        "duty_rules": [10, 11],
        "_relations": {
          "duty_arranges": [...],
          "duty_rules": [...]
        },
        "_metadata": {
          "resource_type": "user_group",
          "original_id": 456
        }
      }
    ],
    "strategy": [
      {
        "id": 123,
        "name": "CPU告警",
        "bk_biz_id": 2,
        "user_groups": [456],
        "action_config_id": 789,
        "_relations": {
          "items": [...],
          "detects": [...],
          "algorithms": [...]
        },
        "_metadata": {
          "resource_type": "strategy",
          "original_id": 123
        }
      }
    ]
  },
  "metadata": {
    "export_summary": {
      "action_plugin": 1,
      "user_group": 1,
      "strategy": 1
    },
    "adapters_applied": [
      "biz_id_mapping",
      "user_mapping"
    ]
  }
}
```

---

## 总结

### 核心设计原则

1. **完整性**: 导出所有必要的数据和关联关系
2. **可追溯**: 通过 `_metadata` 记录原始ID和资源类型
3. **可扩展**: 通过 `version` 支持格式演进
4. **可读性**: 使用JSON格式，便于人工检查和调试
5. **依赖管理**: 按照依赖顺序组织资源

### 关键字段总结

| 字段 | 层级 | 必需 | 作用 |
|------|------|------|------|
| `version` | 顶层 | ✅ | 格式版本标识 |
| `export_time` | 顶层 | ✅ | 导出时间戳 |
| `source_env` | 顶层 | ✅ | 来源环境标识 |
| `resources` | 顶层 | ✅ | 所有资源数据 |
| `metadata` | 顶层 | ✅ | 导出元数据 |
| `_relations` | 对象内 | ❌ | 关联对象数据（仅从属资源） |
| `_metadata` | 对象内 | ✅ | 对象元数据 |
| `export_summary` | metadata内 | ✅ | 导出统计信息 |
| `adapters_applied` | metadata内 | ✅ | 应用的适配器 |

### 使用场景

1. **全量迁移**: 将整个监控配置从一个环境迁移到另一个环境
2. **备份恢复**: 定期备份监控配置，需要时恢复
3. **配置复制**: 将某个业务的配置复制到另一个业务
4. **版本管理**: 跟踪配置变更历史
5. **审计追溯**: 记录配置导出/导入操作
