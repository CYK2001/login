# API文档

## 1. 认证接口

### 1.1 生成验证码
- **URL**: `/api/captcha`
- **方法**: `GET`
- **描述**: 生成登录验证码
- **请求参数**: 无
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "成功",
    "data": {
      "captcha_id": "some-id",
      "image_data": "base64-encoded-image"
    }
  }
  ```

### 1.2 用户登录
- **URL**: `/api/login`
- **方法**: `POST`
- **描述**: 用户登录
- **请求参数**:
  ```json
  {
    "username": "admin",
    "password": "123456",
    "captcha": "2873"
  }
  ```
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "登录成功",
    "data": {
      "token": "jwt-token"
    }
  }
  ```

### 1.3 用户登出
- **URL**: `/api/logout`
- **方法**: `POST`
- **描述**: 用户登出
- **请求参数**: 无
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "登出成功"
  }
  ```

## 2. 用户管理接口

### 2.1 获取用户列表
- **URL**: `/api/users`
- **方法**: `GET`
- **描述**: 获取用户列表，支持分页、搜索和排序
- **请求参数**:
  - `page`: 页码，默认1
  - `page_size`: 每页数量，默认10
  - `search`: 搜索关键词
  - `username`: 用户名搜索
  - `name`: 姓名搜索
  - `role`: 角色搜索
  - `sortBy`: 排序字段，默认created_at
  - `sortOrder`: 排序顺序，默认desc
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "获取用户列表成功",
    "data": {
      "total": 100,
      "total_pages": 10,
      "users": [
        {
          "id": 1,
          "username": "admin",
          "name": "管理员",
          "email": "admin@example.com",
          "phone": "13800138000",
          "gender": "男",
          "role": "管理员",
          "created_at": "2023-01-01 00:00:00"
        }
      ]
    }
  }
  ```

### 2.2 获取单个用户
- **URL**: `/api/users/{user_id}`
- **方法**: `GET`
- **描述**: 获取单个用户详情
- **请求参数**: 无
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "获取用户信息成功",
    "data": {
      "user": {
        "id": 1,
        "username": "admin",
        "name": "管理员",
        "email": "admin@example.com",
        "phone": "13800138000",
        "gender": "男",
        "role": "管理员",
        "created_at": "2023-01-01 00:00:00"
      }
    }
  }
  ```

### 2.3 创建用户
- **URL**: `/api/users`
- **方法**: `POST`
- **描述**: 创建新用户
- **请求参数**:
  ```json
  {
    "username": "newuser",
    "password": "123456",
    "name": "新用户",
    "email": "newuser@example.com",
    "phone": "13900139000",
    "gender": "男",
    "role": "普通用户"
  }
  ```
- **响应示例**:
  ```json
  {
    "code": 201,
    "msg": "用户创建成功"
  }
  ```

### 2.4 更新用户
- **URL**: `/api/users/{user_id}`
- **方法**: `PUT`
- **描述**: 更新用户信息
- **请求参数**:
  ```json
  {
    "name": "更新后的用户名",
    "email": "updated@example.com",
    "phone": "13900139001",
    "gender": "女",
    "role": "管理员"
  }
  ```
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "用户更新成功"
  }
  ```

### 2.5 删除用户
- **URL**: `/api/users/{user_id}`
- **方法**: `DELETE`
- **描述**: 删除用户
- **请求参数**: 无
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "用户删除成功"
  }
  ```

### 2.6 批量删除用户
- **URL**: `/api/users/bulk-delete`
- **方法**: `POST`
- **描述**: 批量删除用户
- **请求参数**:
  ```json
  {
    "user_ids": [1, 2, 3]
  }
  ```
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "批量删除用户成功"
  }
  ```

### 2.7 重置用户密码
- **URL**: `/api/users/{user_id}/reset-password`
- **方法**: `POST`
- **描述**: 重置用户密码
- **请求参数**:
  ```json
  {
    "new_password": "newpassword123"
  }
  ```
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "密码重置成功"
  }
  ```

### 2.8 批量重置用户密码
- **URL**: `/api/users/bulk-reset-password`
- **方法**: `POST`
- **描述**: 批量重置用户密码
- **请求参数**:
  ```json
  {
    "user_ids": [1, 2, 3],
    "new_password": "newpassword123"
  }
  ```
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "批量重置密码成功",
    "data": {
      "reset_count": 3
    }
  }
  ```

## 3. 角色管理接口

### 3.1 获取角色列表
- **URL**: `/api/roles`
- **方法**: `GET`
- **描述**: 获取角色列表，支持分页和搜索
- **请求参数**:
  - `page`: 页码，默认1
  - `page_size`: 每页数量，默认10
  - `search`: 搜索关键词
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "获取角色列表成功",
    "data": {
      "total": 10,
      "roles": [
        {
          "id": 1,
          "role": "管理员",
          "permissions": ["用户管理", "角色管理", "审计日志管理"],
          "is_in_use": true,
          "created_at": "2023-01-01 00:00:00"
        }
      ],
      "total_pages": 1
    }
  }
  ```

### 3.2 获取单个角色
- **URL**: `/api/roles/{role_id}`
- **方法**: `GET`
- **描述**: 获取单个角色详情
- **请求参数**: 无
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "获取角色信息成功",
    "data": {
      "id": 1,
      "role": "管理员",
      "permissions": ["用户管理", "角色管理", "审计日志管理"],
      "is_in_use": true,
      "created_at": "2023-01-01 00:00:00"
    }
  }
  ```

### 3.3 获取权限列表
- **URL**: `/api/permissions`
- **方法**: `GET`
- **描述**: 获取所有权限列表
- **请求参数**: 无
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "获取权限列表成功",
    "data": [
      {"id": 1, "permissions": "用户管理"},
      {"id": 2, "permissions": "角色管理"},
      {"id": 3, "permissions": "审计日志管理"}
    ]
  }
  ```

### 3.4 创建角色
- **URL**: `/api/roles`
- **方法**: `POST`
- **描述**: 创建新角色
- **请求参数**:
  ```json
  {
    "name": "新角色",
    "permissions": ["用户管理", "角色管理"]
  }
  ```
- **响应示例**:
  ```json
  {
    "code": 201,
    "msg": "角色创建成功"
  }
  ```

### 3.5 更新角色
- **URL**: `/api/roles/{role_id}`
- **方法**: `PUT`
- **描述**: 更新角色信息
- **请求参数**:
  ```json
  {
    "name": "更新后的角色",
    "permissions": ["用户管理", "角色管理", "审计日志管理"]
  }
  ```
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "角色更新成功"
  }
  ```

### 3.6 删除角色
- **URL**: `/api/roles/{role_id}`
- **方法**: `DELETE`
- **描述**: 删除角色
- **请求参数**: 无
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "角色删除成功"
  }
  ```

### 3.7 批量删除角色
- **URL**: `/api/roles/bulk-delete`
- **方法**: `POST`
- **描述**: 批量删除角色
- **请求参数**:
  ```json
  {
    "role_ids": [1, 2, 3]
  }
  ```
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "批量删除角色成功"
  }
  ```

## 4. 个人信息接口

### 4.1 获取个人信息
- **URL**: `/api/profile`
- **方法**: `GET`
- **描述**: 获取当前用户个人信息
- **请求参数**: 无
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "获取个人信息成功",
    "data": {
      "id": 1,
      "username": "admin",
      "role": "管理员",
      "name": "管理员",
      "phone": "13800138000",
      "email": "admin@example.com",
      "created_at": "2023-01-01 00:00:00",
      "avatar": "admin.jpg"
    }
  }
  ```

### 4.2 更新个人信息
- **URL**: `/api/profile`
- **方法**: `PUT`
- **描述**: 更新当前用户个人信息
- **请求参数**:
  ```json
  {
    "name": "管理员",
    "phone": "13800138001",
    "email": "admin@example.com"
  }
  ```
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "更新个人信息成功"
  }
  ```

### 4.3 修改密码
- **URL**: `/api/profile/change_password`
- **方法**: `POST`
- **描述**: 修改当前用户密码
- **请求参数**:
  ```json
  {
    "old_password": "123456",
    "new_password": "newpassword123",
    "confirm_password": "newpassword123"
  }
  ```
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "密码修改成功，请重新登录"
  }
  ```

### 4.4 获取用户权限
- **URL**: `/api/profile/permissions`
- **方法**: `GET`
- **描述**: 获取当前用户权限
- **请求参数**: 无
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "获取用户权限成功",
    "data": {
      "role": "管理员",
      "permissions": ["用户管理", "角色管理", "审计日志管理"]
    }
  }
  ```

### 4.5 更新头像
- **URL**: `/api/profile/update`
- **方法**: `POST`
- **描述**: 更新当前用户头像
- **请求参数**: 表单数据，包含avatar文件
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "头像上传成功",
    "data": {
      "avatar": "admin.jpg"
    }
  }
  ```

## 5. 审计日志接口

### 5.1 获取审计日志列表
- **URL**: `/api/audit_logs`
- **方法**: `GET`
- **描述**: 获取审计日志列表，支持分页和搜索
- **请求参数**:
  - `page`: 页码，默认1
  - `page_size`: 每页数量，默认10
  - `search`: 搜索关键词
  - `action`: 操作类型
  - `username`: 用户名
  - `target`: 操作目标
  - `details`: 操作详情
  - `start_time`: 开始时间
  - `end_time`: 结束时间
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "获取审计日志列表成功",
    "data": {
      "total": 1000,
      "logs": [
        {
          "id": 1,
          "username": "admin",
          "action": "登录",
          "target": "系统",
          "details": {"result": "成功"},
          "ip_address": "127.0.0.1",
          "created_at": "2023-01-01 00:00:00"
        }
      ],
      "page": 1,
      "page_size": 10,
      "total_pages": 100
    }
  }
  ```

### 5.2 获取审计日志详情
- **URL**: `/api/audit_logs/{log_id}`
- **方法**: `GET`
- **描述**: 获取审计日志详情
- **请求参数**: 无
- **响应示例**:
  ```json
  {
    "code": 200,
    "msg": "获取审计日志详情成功",
    "data": {
      "id": 1,
      "username": "admin",
      "action": "登录",
      "target": "系统",
      "details": {"result": "成功"},
      "ip_address": "127.0.0.1",
      "created_at": "2023-01-01 00:00:00"
    }
  }
  ```

### 5.3 导出审计日志
- **URL**: `/api/audit_logs/export`
- **方法**: `GET`
- **描述**: 导出审计日志为CSV文件
- **请求参数**:
  - 与获取审计日志列表相同的过滤参数
- **响应示例**: CSV文件下载

## 6. 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权或登录失败 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
