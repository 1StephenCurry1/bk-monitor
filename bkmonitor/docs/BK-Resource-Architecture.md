# BK-Resource 架构指南

## 概述

BK-Resource 是一个基于 DRF（Django REST Framework）的自定义 API 框架，提供了更灵活的资源路由和业务逻辑组织方式。

## 核心概念

### Resource 基础

使用 Resource 实现一个简单的 API：

1. **继承 Resource**
   - 在 `resource.py` 中编写 Resource 类
   - 逻辑不再写在 `view.py` 中，而是在 Resource 中

2. **编写序列化器**
   - 可以内置在 Resource 中或编写在 `serializer.py`
   - 包括请求验证和响应格式化

3. **实现 perform_request 方法**
   - 参数为 `validated_request_data`
   - 直接返回处理结果

4. **在 view.py 中注册逻辑**
   - 将编写好的 Resource 注册到 ViewSet 中

## 核心组件

### PermissionMixin

权限类，根据请求的不同方法（GET/POST）提供不同的权限。

### ResourceViewSet

基于 DRF 的自定义视图集，特点：

- 继承自 `viewsets.ViewSet`
- 提供资源路由功能
- 路径组合规则：`/<module_name>/<custom_path>/<viewset_name>/<endpoint>`

### 路径组合规则解析

```
/<module_name>/<custom_path>/<viewset_name>/<endpoint>
```

- **module_name**：取自 modules 目录下的包名（如：default）
- **custom_path**：取自 urls 文件中配置的路由前缀
- **viewset_name**：ViewSet 的前缀转换为小写下划线连接
  - 例如：`UserInfoViewSet` → `user_info`
- **endpoint**：未配置时与 Restful 结构一致，配置后以指定的为准
  - 注意：一个 endpoint 只能对应一种请求方式

## 序列化器

### RequestSerializer 和 ResponseSerializer

在 Resource 中提供两个参数用于指定输入输出的序列化器：

- **RequestSerializer**：校验用户请求数据
  - 校验后的数据放置在 `perform_request` 方法的 `validated_request_data` 参数中

- **ResponseSerializer**：格式化响应数据
  - 响应时通过 ResponseSerializer 格式化后，再封装为 Response 对象

## 使用 DRF 的存在的问题

BK-Resource 框架试图解决的问题：

1. **过度关注 Model 的 CRUD 操作**
   - 实际开发中存在很多不涉及 model 的业务代码

2. **参数接收方式限制**
   - DRF 接受参数为 request，基于请求开发
   - 无法直接进行逻辑复用

3. **数据校验与业务逻辑耦合**
   - 数据校验逻辑与业务逻辑无法分离（`serializer.is_valid()`）

## Resource 的调用方式

### 直接调用 Resource

```python
# 基础调用
resource.{package_name}.{resource_name}.request(**kwargs)

# 多线程执行
resource.{package_name}.{resource_name}.bulk_request(**kwargs)

# 缓存支持
resource.{package_name}.{resource_name}.cached(**kwargs)

# 异步支持
resource.{package_name}.{resource_name}.delay(**kwargs)
```

### 调用约定

当应用启动后，所有 Resource 类的对象都会被挂载在 resource 上，调用方法为：

```python
resource.{包名}.{小写下划线分割的类名}
```

如果有多层包，都需要写出来：

```python
resource.{包名}.{包名}.…….{包名}.{小写下划线分割的类名}
```

### 示例

```python
resource_routes = [
    # common
    # 获取全部监控场景
    ResourceRoute("GET", 
                  resource.strategies.get_scenario_list, 
                  endpoint="get_scenario_list")
]
```

## 返回值处理

### 返回单条数据

- 支持直接返回 `dict`，会被包装为 data 字段的属性
- 返回 ORM Model 对象（必须提供 ResponseSerializer 且继承自 ModelSerializer）

### 返回多条数据

需要在 Resource 类中声明 `many_response_data = True`

**支持的返回类型：**

1. 列表，其中每一个元素是符合 ResponseSerializer 格式的 dict 对象
2. ORM Model QuerySet（必须提供 ResponseSerializer 且继承自 ModelSerializer）

**示例：**

```python
class AnotherResource(Resource):
    many_response_data = True
    
    class RequestSerializer(serializers.Serializer):
        username = serializers.CharField(required=True)
    
    class ResponseSerializer(serializers.ModelSerializer):
        class Meta:
            model = UserInfo
            fields = '__all__'
    
    def perform_request(self, validated_request_data):
        users = UserInfo.objects.filter(username=validated_request_data["username"])
        # 返回对象集合
        return users
```

## ViewSet 定义

### 基础结构

```python
# view.py
# 声明 ViewSet，其中，ViewSet前方的内容会成为 url 的一部分
class UserInfoViewSet(ResourceViewSet):
    # 声明所有方法
    # Resource 会自动查找所有的子类并添加到 resource 中
    # 映射关系为 underscore_to_camel; 即 UpdateUserInfo => update_user_info
    resource_routes = [
        # 在这一条路由中，app0 为包名，update_user_info 为 app0 下 resources.py 文件中的 UpdateUserInfoResource 对象
        # endpoint 不填写时默认为空，映射为根路由
        ResourceRoute("POST", resource.app0.update_user_info, endpoint="info"),
        
        # 也可以使用常规的方式进行声明，但不推荐
        ResourceRoute("POST", UpdateUserInfoResource),
        
        # 如果涉及到了 RestFul 标准的更新、删除类型，可以使用 pk_field 声明
        # 会自动将 pk 添加到 validated_request_data 中
        ResourceRoute("PUT", UpdateUserInfoResource, pk_field="user_id"),
    ]
```

## ResourceRoute 配置属性

| 属性 | 说明 | 必需 |
|------|------|------|
| method | 请求方法，支持 GET、POST、PUT、PATCH、DELETE | 是 |
| resource_class | 需要调用的 Resource 类 | 是 |
| endpoint | 定义追加的 url 后缀。如 TestViewSet 中定义 endpoint 为 my_endpoint，则访问链接为 `.../test/my_endpoint/`；若不定义则为 `.../test/` | 否 |
| enable_paginate | 是否启动分页功能，当对应的 Resource 配置了 `many_response_data = True` 才有效 | 否 |
| pk_field | 定义主键字段名，会自动将 pk 添加到 `validated_request_data` 中 | 否 |

### 分页处理

**自动分页：** 设置 `enable_paginate=True`

**手动分页：** 在 resource 中手动处理分页逻辑

```python
return list[(params["page"] - 1) * params["page_size"] : params["page"] * params["page_size"]]
```

## 完整示例

### Resource 定义

```python
# resources.py
from rest_framework import serializers
from packages.bk_monitor.resource import Resource

class GetUserListResource(Resource):
    many_response_data = True
    
    class RequestSerializer(serializers.Serializer):
        page = serializers.IntegerField(required=False, default=1)
        page_size = serializers.IntegerField(required=False, default=10)
        username = serializers.CharField(required=False, allow_blank=True)
    
    class ResponseSerializer(serializers.ModelSerializer):
        class Meta:
            model = UserInfo
            fields = ['id', 'username', 'email']
    
    def perform_request(self, validated_request_data):
        page = validated_request_data.get('page', 1)
        page_size = validated_request_data.get('page_size', 10)
        username = validated_request_data.get('username', '')
        
        queryset = UserInfo.objects.all()
        if username:
            queryset = queryset.filter(username__icontains=username)
        
        start = (page - 1) * page_size
        end = start + page_size
        return queryset[start:end]
```

### ViewSet 定义

```python
# views.py
from packages.bk_monitor.resource import ResourceViewSet, ResourceRoute
from . import resources

class UserInfoViewSet(ResourceViewSet):
    resource_routes = [
        ResourceRoute("GET", resources.GetUserListResource, endpoint="list"),
    ]
```

### URL 配置

```python
# urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from . import views

router = SimpleRouter()
router.register('users', views.UserInfoViewSet, basename='user_info')

urlpatterns = [
    path('api/', include(router.urls)),
]
```

## 最佳实践

1. **逻辑分离**
   - 业务逻辑放在 Resource 中的 `perform_request` 方法
   - 数据校验由 Serializer 负责

2. **复用性**
   - Resource 可以直接调用，无需通过 HTTP 请求
   - 便于在其他地方复用相同的业务逻辑

3. **权限控制**
   - 使用 PermissionMixin 为不同的请求方法配置权限
   - 确保 API 的安全性

4. **错误处理**
   - 在 `perform_request` 中进行业务校验和错误处理
   - 返回有意义的错误信息
