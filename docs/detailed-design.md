# AIQAHub 详细设计文档

## 目录

1. [数据库详细设计](#1-数据库详细设计)
2. [API 详细设计](#2-api-详细设计)
3. [核心业务流程设计](#3-核心业务流程设计)

---

## 1. 数据库详细设计

### 1.1 ER 图

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│    users    │         │   roles     │         │environments │
│ (用户表)    │         │  (角色表)   │         │  (环境表)    │
└─────────────┘         └─────────────┘         └─────────────┘
       │                        │                        │
       │                        │                        │
       └──────────┬───────────┘                        │
                  │                                    │
                  ▼                                    │
         ┌──────────────┐                               │
         │user_roles   │                               │
         │ (用户角色关│                               │
         └──────────────┘                               │
                  │                                    │
┌─────────────────┼────────────────────────────────────┘
│                 │
│    ┌────────────▼────────────┐
│    │     projects         │
│    │     (项目表)         │
│    └─────────────────────┘
│               │
│    ┌──────────┼──────────┐
│    │          │          │
│    ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│suites   │ │quality  │ │assets │
│(测试套件)│ │rules    │ │(资产表) │
└─────────┘ └─────────┘ └─────────┘
     │            │            │
     │            │            │
     ▼            │            │
┌──────────┐        │            │
│executions│        │            │
│(执行表)  │◄───────┘            │
└──────────┘                     │
     │                           │
     ├───────────────────────────┤
     │                           │
     ▼                           ▼
┌──────────┐              ┌──────────┐
│artifacts │              │tasks    │
│(产物表)  │              │(任务表)  │
└──────────┘              └──────────┘
     │
     ▼
┌──────────┐
│gate_evals │
│(门禁评估)│
└──────────┘

┌─────────────────────────────────────────┐
│         audit_logs                    │
│         (审计日志表)                  │
└─────────────────────────────────────────┘
```

### 1.2 表结构详解

#### 1.2.1 users (用户表)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(64) | PK | 用户 ID |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 邮箱 |
| username | VARCHAR(128) | UNIQUE, NOT NULL | 用户名 |
| hashed_password | VARCHAR(255) | NOT NULL | 加密密码 |
| full_name | VARCHAR(255) | NULL | 全名 |
| avatar_url | VARCHAR(512) | NULL | 头像 URL |
| status | VARCHAR(32) | DEFAULT 'active' | 状态: active/inactive |
| settings_json | JSON | NULL | 用户设置 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

**索引:**
- `idx_users_email` ON users(email)
- `idx_users_username` ON users(username)

---

#### 1.2.2 roles (角色表)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(64) | PK | 角色 ID |
| name | VARCHAR(128) | UNIQUE, NOT NULL | 角色名称 |
| description | TEXT | NULL | 角色描述 |
| permissions_json | JSON | NOT NULL | 权限列表 |
| is_system | BOOLEAN | DEFAULT FALSE | 是否系统角色 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

**预置角色:**
- `admin`: 平台管理员
- `owner`: 项目所有者
- `member`: 项目成员
- `viewer`: 只读访问

---

#### 1.2.3 user_roles (用户角色关联表)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(64) | PK | ID |
| user_id | VARCHAR(64) | FK, NOT NULL | 用户 ID |
| role_id | VARCHAR(64) | FK, NOT NULL | 角色 ID |
| project_id | VARCHAR(64) | FK, NULL | 项目 ID (全局角色为空) |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

**索引:**
- `idx_user_roles_user` ON user_roles(user_id)
- `idx_user_roles_role` ON user_roles(role_id)
- `idx_user_roles_project` ON user_roles(project_id)

---

#### 1.2.4 environments (环境表)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(64) | PK | 环境 ID |
| name | VARCHAR(128) | NOT NULL | 环境名称 |
| code | VARCHAR(64) | UNIQUE, NOT NULL | 环境代码 |
| description | TEXT | NULL | 环境描述 |
| config_json | JSON | NULL | 环境配置 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

---

#### 1.2.5 projects (项目表)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(64) | PK | 项目 ID |
| code | VARCHAR(64) | UNIQUE, NOT NULL | 项目编码 |
| name | VARCHAR(255) | NOT NULL | 项目名称 |
| description | TEXT | NULL | 项目描述 |
| owner_id | VARCHAR(64) | FK, NULL | 所有者用户 ID |
| status | VARCHAR(32) | DEFAULT 'active' | 状态 |
| default_env_id | VARCHAR(64) | FK, NULL | 默认环境 ID |
| settings_json | JSON | NULL | 项目设置 |
| metadata_json | JSON | NULL | 元数据 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

**索引:**
- `idx_projects_code` ON projects(code)
- `idx_projects_owner` ON projects(owner_id)
- `idx_projects_status` ON projects(status)

---

#### 1.2.6 test_suites (测试套件表)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(64) | PK | 套件 ID |
| project_id | VARCHAR(64) | FK, NOT NULL | 项目 ID |
| name | VARCHAR(255) | NOT NULL | 套件名称 |
| suite_type | VARCHAR(32) | NOT NULL | 套件类型: unittest/e2e/performance/security |
| source_type | VARCHAR(32) | NOT NULL | 源类型: git/jenkins/local |
| source_ref | TEXT | NOT NULL | 源引用 |
| default_env_id | VARCHAR(64) | FK, NULL | 默认环境 ID |
| connector_config_json | JSON | NULL | 连接器配置 |
| metadata_json | JSON | NULL | 元数据 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

**索引:**
- `idx_suites_project` ON test_suites(project_id)
- `idx_suites_type` ON test_suites(suite_type)

---

#### 1.2.7 executions (执行表)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(64) | PK | 执行 ID |
| project_id | VARCHAR(64) | FK, NOT NULL | 项目 ID |
| suite_id | VARCHAR(64) | FK, NOT NULL | 套件 ID |
| env_id | VARCHAR(64) | FK, NOT NULL | 环境 ID |
| trigger_type | VARCHAR(32) | NOT NULL | 触发类型: manual/webhook/schedule/api |
| trigger_source | VARCHAR(128) | NULL | 触发源 |
| status | VARCHAR(32) | DEFAULT 'created' | 状态: created/queued/running/completed/failed/timeout/cancelled |
| request_params_json | JSON | NULL | 请求参数 |
| summary_json | JSON | NULL | 执行摘要 |
| error_message | TEXT | NULL | 错误信息 |
| started_at | TIMESTAMP | NULL | 开始时间 |
| completed_at | TIMESTAMP | NULL | 结束时间 |
| duration_seconds | INTEGER | NULL | 耗时(秒) |
| created_by | VARCHAR(64) | FK, NULL | 创建者 ID |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

**状态流转:**
```
created → queued → running → completed
                    ↓
              failed / timeout / cancelled
```

**索引:**
- `idx_executions_project` ON executions(project_id)
- `idx_executions_suite` ON executions(suite_id)
- `idx_executions_env` ON executions(env_id)
- `idx_executions_status` ON executions(status)
- `idx_executions_created` ON executions(created_at DESC)

---

#### 1.2.8 execution_tasks (执行任务表)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(64) | PK | 任务 ID |
| execution_id | VARCHAR(64) | FK, NOT NULL | 执行 ID |
| task_key | VARCHAR(128) | NOT NULL | 任务键 |
| task_name | VARCHAR(255) | NOT NULL | 任务名称 |
| status | VARCHAR(32) | DEFAULT 'pending' | 状态 |
| worker_id | VARCHAR(64) | NULL | 工作节点 ID |
| input_json | JSON | NULL | 输入数据 |
| output_json | JSON | NULL | 输出数据 |
| error_message | TEXT | NULL | 错误信息 |
| started_at | TIMESTAMP | NULL | 开始时间 |
| completed_at | TIMESTAMP | NULL | 结束时间 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

**索引:**
- `idx_tasks_execution` ON execution_tasks(execution_id)
- `idx_tasks_status` ON execution_tasks(status)

---

#### 1.2.9 execution_artifacts (执行产物表)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(64) | PK | 产物 ID |
| execution_id | VARCHAR(64) | FK, NOT NULL | 执行 ID |
| artifact_type | VARCHAR(64) | NOT NULL | 产物类型: report/junit/playwright/log/screenshot/video |
| name | VARCHAR(255) | NOT NULL | 产物名称 |
| storage_uri | TEXT | NOT NULL | 存储 URI |
| mime_type | VARCHAR(128) | NULL | MIME 类型 |
| file_size_bytes | BIGINT | NULL | 文件大小(字节) |
| metadata_json | JSON | NULL | 元数据 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

**索引:**
- `idx_artifacts_execution` ON execution_artifacts(execution_id)
- `idx_artifacts_type` ON execution_artifacts(artifact_type)

---

#### 1.2.10 quality_rules (质量规则表)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(64) | PK | 规则 ID |
| project_id | VARCHAR(64) | FK, NOT NULL | 项目 ID |
| name | VARCHAR(255) | NOT NULL | 规则名称 |
| rule_type | VARCHAR(64) | NOT NULL | 规则类型: pass_rate/failure_count/coverage/flaky_rate/custom |
| enabled | BOOLEAN | DEFAULT TRUE | 是否启用 |
| severity | VARCHAR(32) | DEFAULT 'warning' | 严重程度: info/warning/error/blocking |
| config_json | JSON | NOT NULL | 规则配置 |
| expression | TEXT | NULL | 规则表达式 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

**规则配置示例 (config_json):**
```json
{
  "pass_rate": {
    "operator": ">=",
    "value": 95.0
  }
}
```

**索引:**
- `idx_rules_project` ON quality_rules(project_id)
- `idx_rules_type` ON quality_rules(rule_type)
- `idx_rules_enabled` ON quality_rules(enabled)

---

#### 1.2.11 quality_rule_revisions (质量规则修订表)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(64) | PK | 修订 ID |
| rule_id | VARCHAR(64) | FK, NOT NULL | 规则 ID |
| revision_number | INTEGER | NOT NULL | 修订号 |
| name | VARCHAR(255) | NOT NULL | 规则名称快照 |
| config_json | JSON | NOT NULL | 规则配置快照 |
| changed_by | VARCHAR(64) | FK, NULL | 修改者 ID |
| change_note | TEXT | NULL | 修改说明 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

**索引:**
- `idx_revisions_rule` ON quality_rule_revisions(rule_id)
- `idx_revisions_number` ON quality_rule_revisions(rule_id, revision_number DESC)

---

#### 1.2.12 gate_evaluations (门禁评估表)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(64) | PK | 评估 ID |
| execution_id | VARCHAR(64) | FK, NOT NULL | 执行 ID |
| status | VARCHAR(32) | NOT NULL | 结果: pass/warning/fail |
| summary_json | JSON | NOT NULL | 评估摘要 |
| evaluated_at | TIMESTAMP | DEFAULT NOW() | 评估时间 |

**评估摘要示例:**
```json
{
  "total_rules": 5,
  "passed_rules": 4,
  "warning_rules": 0,
  "failed_rules": 1,
  "rule_results": [
    {
      "rule_id": "xxx",
      "rule_name": "Pass Rate",
      "status": "pass",
      "actual": 98.5,
      "expected": ">= 95.0"
    }
  ]
}
```

**索引:**
- `idx_evaluations_execution` ON gate_evaluations(execution_id)
- `idx_evaluations_status` ON gate_evaluations(status)

---

#### 1.2.13 assets (资产表)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(64) | PK | 资产 ID |
| project_id | VARCHAR(64) | FK, NOT NULL | 项目 ID |
| name | VARCHAR(255) | NOT NULL | 资产名称 |
| asset_type | VARCHAR(64) | NOT NULL | 资产类型: test_data/config/script |
| description | TEXT | NULL | 资产描述 |
| current_revision_id | VARCHAR(64) | FK, NULL | 当前版本 ID |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

**索引:**
- `idx_assets_project` ON assets(project_id)
- `idx_assets_type` ON assets(asset_type)

---

#### 1.2.14 asset_revisions (资产版本表)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(64) | PK | 版本 ID |
| asset_id | VARCHAR(64) | FK, NOT NULL | 资产 ID |
| revision_number | INTEGER | NOT NULL | 版本号 |
| content_json | JSON | NULL | 内容(JSON) |
| content_text | TEXT | NULL | 内容(文本) |
| storage_uri | TEXT | NULL | 存储 URI |
| created_by | VARCHAR(64) | FK, NULL | 创建者 ID |
| change_note | TEXT | NULL | 修改说明 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

**索引:**
- `idx_rev_asset` ON asset_revisions(asset_id)
- `idx_rev_number` ON asset_revisions(asset_id, revision_number DESC)

---

#### 1.2.15 asset_links (资产关联表)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(64) | PK | ID |
| asset_id | VARCHAR(64) | FK, NOT NULL | 资产 ID |
| target_type | VARCHAR(64) | NOT NULL | 目标类型 |
| target_id | VARCHAR(64) | NOT NULL | 目标 ID |
| link_type | VARCHAR(64) | NOT NULL | 关联类型 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

**索引:**
- `idx_links_asset` ON asset_links(asset_id)
- `idx_links_target` ON asset_links(target_type, target_id)

---

#### 1.2.16 ai_insights (AI 洞察表)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(64) | PK | 洞察 ID |
| execution_id | VARCHAR(64) | FK, NOT NULL | 执行 ID |
| insight_type | VARCHAR(64) | NOT NULL | 洞察类型 |
| provider | VARCHAR(64) | NOT NULL | AI 提供商 |
| model | VARCHAR(128) | NOT NULL | 模型名称 |
| content_json | JSON | NOT NULL | 洞察内容 |
| prompt_tokens | INTEGER | NULL | Prompt token 数 |
| completion_tokens | INTEGER | NULL | 完成 token 数 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

**洞察内容示例:**
```json
{
  "root_cause": "数据库连接超时",
  "suggestion": "检查数据库连接池配置",
  "confidence": 0.85,
  "similar_failures": ["exec-xxx", "exec-yyy"]
}
```

**索引:**
- `idx_insights_execution` ON ai_insights(execution_id)
- `idx_insights_type` ON ai_insights(insight_type)

---

#### 1.2.17 audit_logs (审计日志表)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(64) | PK | 日志 ID |
| actor_id | VARCHAR(64) | FK, NULL | 操作者 ID |
| action | VARCHAR(128) | NOT NULL | 操作类型 |
| target_type | VARCHAR(64) | NOT NULL | 目标类型 |
| target_id | VARCHAR(64) | NOT NULL | 目标 ID |
| request_json | JSON | NULL | 请求数据 |
| response_json | JSON | NULL | 响应数据 |
| note | TEXT | NULL | 备注 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

**操作类型 (action):**
- `project.create`, `project.update`, `project.delete`
- `execution.create`, `execution.start`, `execution.complete`
- `gate.evaluate`, `gate.pass`, `gate.fail`
- `notification.send`, `notification.fail`
- `settings.update`

**索引:**
- `idx_audit_actor` ON audit_logs(actor_id)
- `idx_audit_target` ON audit_logs(target_type, target_id)
- `idx_audit_action` ON audit_logs(action)
- `idx_audit_created` ON audit_logs(created_at DESC)

---

### 1.3 数据库初始化脚本 (SQL)

```sql
-- 核心表创建顺序 (SQLite 方言)

-- 用户表
CREATE TABLE users (
    id VARCHAR(64) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(128) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url VARCHAR(512),
    status VARCHAR(32) DEFAULT 'active',
    settings_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 角色表
CREATE TABLE roles (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) UNIQUE NOT NULL,
    description TEXT,
    permissions_json TEXT NOT NULL,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 项目表
CREATE TABLE projects (
    id VARCHAR(64) PRIMARY KEY,
    code VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id VARCHAR(64),
    status VARCHAR(32) DEFAULT 'active',
    default_env_id VARCHAR(64),
    settings_json TEXT,
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 测试套件表
CREATE TABLE test_suites (
    id VARCHAR(64) PRIMARY KEY,
    project_id VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    suite_type VARCHAR(32) NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    source_ref TEXT NOT NULL,
    default_env_id VARCHAR(64),
    connector_config_json TEXT,
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 执行表
CREATE TABLE executions (
    id VARCHAR(64) PRIMARY KEY,
    project_id VARCHAR(64) NOT NULL,
    suite_id VARCHAR(64) NOT NULL,
    env_id VARCHAR(64) NOT NULL,
    trigger_type VARCHAR(32) NOT NULL,
    trigger_source VARCHAR(128),
    status VARCHAR(32) DEFAULT 'created',
    request_params_json TEXT,
    summary_json TEXT,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    created_by VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 质量规则表
CREATE TABLE quality_rules (
    id VARCHAR(64) PRIMARY KEY,
    project_id VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(64) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    severity VARCHAR(32) DEFAULT 'warning',
    config_json TEXT NOT NULL,
    expression TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 审计日志表
CREATE TABLE audit_logs (
    id VARCHAR(64) PRIMARY KEY,
    actor_id VARCHAR(64),
    action VARCHAR(128) NOT NULL,
    target_type VARCHAR(64) NOT NULL,
    target_id VARCHAR(64) NOT NULL,
    request_json TEXT,
    response_json TEXT,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_projects_code ON projects(code);
CREATE INDEX idx_executions_project ON executions(project_id);
CREATE INDEX idx_executions_status ON executions(status);
CREATE INDEX idx_audit_target ON audit_logs(target_type, target_id);
CREATE INDEX idx_audit_created ON audit_logs(created_at DESC);
```

---

## 2. API 详细设计

### 2.1 API 设计规范

#### 2.1.1 通用响应格式

**成功响应 (200 OK):
```json
{
  "data": { /* 数据内容 */ },
  "meta": {
    "request_id": "req-xxx",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**分页响应 (200 OK):**
```json
{
  "data": [ /* 数据列表 */ ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

**错误响应 (4xx/5xx):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": [
      {
        "field": "name",
        "message": "名称不能为空"
      }
    ]
  }
}
```

#### 2.1.2 标准状态码

| 状态码 | 说明 |
|-------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 422 | 验证失败 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

---

### 2.2 项目 API

#### 2.2.1 获取项目列表

```
GET /api/v1/projects
```

**请求参数:**
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| search | string | 否 | 搜索关键词 |
| status | string | 否 | 状态过滤 |
| owner_id | string | 否 | 所有者过滤 |
| sort | string | 否 | 排序字段: name/created_at |
| sort_order | string | 否 | 排序方向: asc/desc |
| page | int | 否 | 页码, 默认 1 |
| page_size | int | 否 | 每页数量, 默认 20, 最大 200 |

**响应示例:**
```json
{
  "data": [
    {
      "id": "proj-001",
      "code": "my-project",
      "name": "My Project",
      "description": "项目描述",
      "status": "active",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 50
  }
}
```

---

#### 2.2.2 创建项目

```
POST /api/v1/projects
```

**请求体:**
```json
{
  "code": "my-project",
  "name": "My Project",
  "description": "项目描述",
  "default_env_id": "env-dev"
}
```

**响应示例 (201 Created):**
```json
{
  "data": {
    "id": "proj-001",
    "code": "my-project",
    "name": "My Project",
    "description": "项目描述",
    "status": "active",
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

---

#### 2.2.3 获取项目详情

```
GET /api/v1/projects/{project_id}
```

**响应示例:**
```json
{
  "data": {
    "id": "proj-001",
    "code": "my-project",
    "name": "My Project",
    "description": "项目描述",
    "status": "status": "active",
    "owner_id": "user-001",
    "default_env_id": "env-dev",
    "settings": {},
    "metadata": {},
    "stats": {
      "total_executions": 150,
      "success_rate": 92.5,
      "last_execution_at": "2024-01-15T09:00:00Z"
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

---

#### 2.2.4 更新项目

```
PUT /api/v1/projects/{project_id}
```

**请求体:**
```json
{
  "name": "Updated Project Name",
  "description": "更新后的描述",
  "default_env_id": "env-staging"
}
```

---

#### 2.2.5 删除项目

```
DELETE /api/v1/projects/{project_id}
```

---

### 2.3 执行 API

#### 2.3.1 获取执行列表

```
GET /api/v1/executions
```

**请求参数:**
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|
| project_id | string | 否 | 项目 ID |
| suite_id | string | 否 | 套件 ID |
| env_id | string | 否 | 环境 ID |
| status | string | 否 | 状态: created/queued/running/completed/failed |
| trigger_type | string | 否 | 触发类型 |
| started_after | string | 否 | 开始时间之后 |
| started_before | string | 否 | 开始时间之前 |
| sort | string | 否 | 排序字段 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应示例:**
```json
{
  "data": [
    {
      "id": "exec-001",
      "project_id": "proj-001",
      "suite_id": "suite-001",
      "env_id": "env-dev",
      "trigger_type": "manual",
      "status": "completed",
      "summary": {
        "total": 100,
        "passed": 95,
        "failed": 5,
        "skipped": 0,
        "duration_seconds": 180
      },
      "started_at": "2024-01-15T10:00:00Z",
      "completed_at": "2024-01-15T10:03:00Z",
      "created_at": "2024-01-15T09:59:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

---

#### 2.3.2 创建执行

```
POST /api/v1/executions
```

**请求体:**
```json
{
  "project_id": "proj-001",
  "suite_id": "suite-001",
  "env_id": "env-dev",
  "trigger_type": "manual",
  "trigger_source": "web-ui",
  "request_params": {
    "branch": "main",
    "commit": "abc123"
  }
}
```

**响应示例 (201 Created):**
```json
{
  "data": {
    "id": "exec-001",
    "project_id": "proj-001",
    "suite_id": "suite-001",
    "env_id": "env-dev",
    "status": "created",
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

---

#### 2.3.3 获取执行详情

```
GET /api/v1/executions/{execution_id}
```

**响应示例:**
```json
{
  "data": {
    "id": "exec-001",
    "project_id": "proj-001",
    "suite_id": "suite-001",
    "env_id": "env-dev",
    "trigger_type": "manual",
    "trigger_source": "web-ui",
    "status": "completed",
    "request_params": {
      "branch": "main"
    },
    "summary": {
      "total": 100,
      "passed": 95,
      "failed": 5,
      "skipped": 0,
      "duration_seconds": 180
    },
    "error_message": null,
    "started_at": "2024-01-15T10:00:00Z",
    "completed_at": "2024-01-15T10:03:00Z",
    "duration_seconds": 180,
    "created_by": "user-001",
    "created_at": "2024-01-15T09:59:00Z",
    "updated_at": "2024-01-15T10:03:00Z"
  }
}
```

---

#### 2.3.4 触发执行

```
POST /api/v1/executions/{execution_id}/run
```

**响应示例:**
```json
{
  "data": {
    "execution_id": "exec-001",
    "status": "queued",
    "task_id": "task-001",
    "summary": {}
  }
}
```

---

#### 2.3.5 获取执行产物

```
GET /api/v1/executions/{execution_id}/artifacts
```

**响应示例:**
```json
{
  "data": [
    {
      "id": "art-001",
      "execution_id": "exec-001",
      "artifact_type": "report",
      "name": "junit.xml",
      "storage_uri": "s3://bucket/art-001/junit.xml",
      "mime_type": "application/xml",
      "file_size_bytes": 102400,
      "created_at": "2024-01-15T10:03:00Z"
    }
  ]
}
```

---

#### 2.3.6 获取执行任务

```
GET /api/v1/executions/{execution_id}/tasks
```

**响应示例:**
```json
{
  "data": [
    {
      "id": "task-001",
      "execution_id": "exec-001",
      "task_key": "fetch-reports",
      "task_name": "Fetch Reports",
      "status": "completed",
      "input": {},
      "output": {},
      "error_message": null,
      "started_at": "2024-01-15T10:00:00Z",
      "completed_at": "2024-01-15T10:01:00Z"
    }
  ]
}
```

---

#### 2.3.7 获取执行时间线

```
GET /api/v1/executions/{execution_id}/timeline
```

**响应示例:**
```json
{
  "data": [
    {
      "stage": "queued",
      "status": "completed",
      "message": "Execution queued",
      "timestamp": "2024-01-15T10:00:00Z"
    },
    {
      "stage": "running",
      "status": "completed",
      "message": "Execution started",
      "timestamp": "2024-01-15T10:00:05Z"
    },
    {
      "stage": "fetch-reports",
      "status": "completed",
      "message": "Reports fetched",
      "timestamp": "2024-01-15T10:02:00Z"
    },
    {
      "stage": "gate-evaluation",
      "status": "completed",
      "message": "Gate evaluation passed",
      "timestamp": "2024-01-15T10:02:30Z"
    },
    {
      "stage": "completed",
      "status": "completed",
      "message": "Execution completed",
      "timestamp": "2024-01-15T10:03:00Z"
    }
  ]
}
```

---

### 2.4 门禁 API

#### 2.4.1 获取质量规则列表

```
GET /api/v1/gates/rules
```

**请求参数:**
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|
| project_id | string | 是 | 项目 ID |
| enabled | boolean | 否 | 是否启用 |
| rule_type | string | 否 | 规则类型 |

**响应示例:**
```json
{
  "data": [
    {
      "id": "rule-001",
      "project_id": "proj-001",
      "name": "Pass Rate",
      "rule_type": "pass_rate",
      "enabled": true,
      "severity": "error",
      "config": {
        "operator": ">=",
        "value": 95.0
      },
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

#### 2.4.2 创建质量规则

```
POST /api/v1/gates/rules
```

**请求体:**
```json
{
  "project_id": "proj-001",
  "name": "Pass Rate",
  "rule_type": "pass_rate",
  "severity": "error",
  "config": {
    "operator": ">=",
    "value": 95.0
  }
}
```

---

#### 2.4.3 评估门禁

```
POST /api/v1/gates/evaluate
```

**请求体:**
```json
{
  "execution_id": "exec-001"
}
```

**响应示例:**
```json
{
  "data": {
    "id": "eval-001",
    "execution_id": "exec-001",
    "status": "pass",
    "summary": {
      "total_rules": 5,
      "passed_rules": 5,
      "warning_rules": 0,
      "failed_rules": 0,
      "rule_results": [
        {
          "rule_id": "rule-001",
          "rule_name": "Pass Rate",
          "status": "pass",
          "actual": 98.5,
          "expected": ">= 95.0"
        }
      ]
    },
    "evaluated_at": "2024-01-15T10:03:00Z"
  }
}
```

---

### 2.5 AI API

#### 2.5.1 触发 AI 分析

```
POST /api/v1/ai/analyze
```

**请求体:**
```json
{
  "execution_id": "exec-001",
  "analysis_type": "failure_analysis"
}
```

**响应示例 (202 Accepted):**
```json
{
  "data": {
    "insight_id": "insight-001",
    "status": "processing"
  }
}
```

---

#### 2.5.2 获取 AI 分析历史

```
GET /api/v1/ai/history
```

**请求参数:**
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|
| project_id | string | 否 | 项目 ID |
| execution_id | string | 否 | 执行 ID |
| insight_type | string | 否 | 洞察类型 |

---

### 2.6 治理 API

#### 2.6.1 获取治理概览

```
GET /api/v1/governance/overview
```

**响应示例:**
```json
{
  "data": {
    "active_projects": 15,
    "executions_today": 45,
    "execution_success_rate": 92.5,
    "notifications_today": {
      "sent": 120,
      "failed": 3,
      "fallback": 2
    },
    "connectors_health": {
      "healthy": 8,
      "unhealthy": 1,
      "unknown": 0
    },
    "top_failure_categories": [
      { "category": "test_flaky", "count": 15 },
      { "category": "environment", "count": 8 },
      { "category": "test_code", "count": 5 }
    ]
  }
}
```

---

#### 2.6.2 获取治理事件流

```
GET /api/v1/governance/events
```

**请求参数:**
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| event_type | string | 否 | 事件类型 |
| resource_type | string | 否 | 资源类型 |
| after | string | 否 | 时间之后 |
| before | string | 否 | 时间之前 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应示例:**
```json
{
  "data": [
    {
      "id": "event-001",
      "event_type": "execution.failed",
      "resource_type": "execution",
      "resource_id": "exec-001",
      "payload": {
        "project_id": "proj-001",
        "suite_id": "suite-001"
      },
      "timestamp": "2024-01-15T10:03:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 50,
    "total": 1000
  }
}
```

---

#### 2.6.3 获取事件详情

```
GET /api/v1/governance/events/{event_id}
```

---

### 2.7 通知 API

#### 2.7.1 测试通知

```
POST /api/v1/notifications/test
```

**请求体:**
```json
{
  "project_id": "proj-001",
  "event_type": "execution.failed",
  "channels": ["email", "dingtalk"]
}
```

**响应示例:**
```json
{
  "data": {
    "status": "sent",
    "channels": {
      "email": "success",
      "dingtalk": "success"
    }
  }
}
```

---

## 3. 核心业务流程设计

### 3.1 测试执行流程

```
┌─────────────┐
│  用户触发   │
│  创建执行  │
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│ 1. 创建执行记录   │
│  status: created  │
└──────┬─────────────┘
       │
       ▼
┌──────────────────────┐
│ 2. 写入审计日志   │
│ action: create    │
└──────┬─────────────┘
       │
       ▼
┌──────────────────────┐
│ 3. 提交 Celery 任务│
│  status: queued    │
└──────┬─────────────┘
       │
       ▼
┌──────────────────────┐
│ 4. Worker 接收任务  │
│  status: running   │
└──────┬─────────────┘
       │
       ├──────────────────────────┐
       │                          │
       ▼                          ▼
┌──────────────┐        ┌──────────────┐
│ 5. 执行连接器│        │ 6. 轮询状态  │
│    (可选)   │        │ 更新执行状态  │
└──────┬───────┘        └──────┬───────┘
       │                          │
       └──────────┬───────────────┘
                  │
                  ▼
         ┌──────────────────┐
         │ 7. 收集 Artifacts │
         └──────┬───────┘
                │
                ▼
         ┌──────────────────┐
         │ 8. 解析报告    │
         │  (JUnit/Playwright)│
         └──────┬───────┘
                │
                ▼
         ┌──────────────────┐
         │ 9. 评估质量门禁│
         └──────┬───────┘
                │
                ▼
         ┌──────────────────┐
         │ 10. 发送通知    │
         │ (按策略路由)   │
         └──────┬───────┘
                │
                ▼
         ┌──────────────────┐
         │ 11. 更新状态    │
         │ status: completed│
         └──────┬───────┘
                │
                ▼
         ┌──────────────────┐
         │ 12. 写入审计日志│
         └──────────────────┘
```

**详细步骤说明:

**步骤 1-3: 执行创建与排队
- 验证项目和套件存在
- 创建 execution 记录 (status = created)
- 写入审计日志 (action = execution.create)
- 提交 Celery 任务, 更新状态为 queued

**步骤 4-6: 执行运行**
- Worker 接收任务, 更新状态为 running
- 调用连接器执行测试 (可选, 如 Jenkins/Playwright)
- 定期轮询状态并更新

**步骤 7-8: 报告处理**
- 下载并保存 artifacts
- 解析报告格式 (JUnit XML, Playwright JSON)
- 聚合测试结果 (passed/failed/skipped)
- 计算统计数据

**步骤 9: 门禁评估**
- 获取项目启用的质量规则
- 逐条评估规则
- 生成评估结果
- 创建 gate_evaluation 记录

**步骤 10: 通知发送**
- 检查是否需要通知 (失败/超时/门禁失败)
- 查找匹配的通知策略
- 按优先级发送通知
- 记录通知发送结果

**步骤 11-12: 完成**
- 更新执行状态为 completed/failed
- 计算执行耗时
- 写入审计日志

---

### 3.2 通知策略路由流程

```
┌─────────────────┐
│   事件触发      │
│ execution.failed│
└───────┬─────────┘
        │
        ▼
┌─────────────────────────────┐
│ 1. 获取事件上下文        │
│    - event_type        │
│    - project_id        │
│    - severity           │
└───────┬─────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ 2. 查找项目级策略       │
│    scope_type = project │
└───────┬─────────────────┘
        │
    找到? │
        ├─ 是 ──┐
        │          │
        否         ▼
        │    ┌───────────────┐
        │    │ 3. 应用过滤器│
        │    │   filters   │
        │    └───────┬───┘
        │            │
        ▼            │ 匹配?
┌─────────────────┐   ├── 是 ──┐
│ 4. 查找全局策略 │   │         │
│  scope_type=global│   │         ▼
└───────┬─────────┘   │  ┌──────────┐
        │             │  │ 6. 发送 │
        ▼ 找到?      │  │ 通知   │
┌─────────────────┐   │  └─────┬────┘
│ 5. 使用默认    │   │        │
│   通道         │   │        │
└───────┬─────────┘   │        │
        │             │        │
        └─────────────┴────────┘
                      │
                      ▼
            ┌───────────────┐
            │ 7. 记录审计  │
            │    事件      │
            └───────────────┘
```

**策略数据结构:**
```json
{
  "scope_type": "project",
  "scope_id": "proj-001",
  "event_type": "execution.failed",
  "channels": ["dingtalk", "email"],
  "target": "@all",
  "filters": {
    "severity": "critical"
  }
}
```

---

### 3.3 质量门禁评估流程

```
┌─────────────────┐
│  触发评估       │
│  execution_id  │
└───────┬─────────┘
        │
        ▼
┌──────────────────────────┐
│ 1. 获取执行报告      │
│    summary_json      │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────────┐
│ 2. 获取项目启用规则    │
│    enabled = true     │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────────┐
│ 3. 逐条评估规则        │
│    ┌────────────────┐ │
│    │ 对于每个规则:   │ │
│    │ - 提取指标     │ │
│    │ - 计算实际值   │ │
│    │ - 比较期望值   │ │
│    │ - 生成结果     │ │
│    └────────────────┘ │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────────┐
│ 4. 聚合评估结果      │
│    - total_rules      │
│    - passed_rules   │
│    - failed_rules   │
│    - 最终状态        │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────────┐
│ 5. 创建评估记录      │
│    gate_evaluation   │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────────┐
│ 6. 写入审计日志        │
│    action: gate.evaluate│
└───────┬──────────────┘
        │
        ▼
┌──────────────────────────┐
│ 7. 返回评估结果        │
│    status: pass/fail  │
└──────────────────────────┘
```

**规则评估逻辑:**

| 规则类型 | 指标提取 | 评估逻辑 |
|---------|---------|---------|
| pass_rate | passed / total | `actual >= config.value` |
| failure_count | failed | `actual <= config.value` |
| flaky_rate | flaky / total | `actual <= config.value` |
| coverage_line | line_coverage | `actual >= config.value` |
| custom | 自定义表达式 | eval(expression) |

---

### 3.4 AI 失败分析流程

```
┌─────────────────┐
│  触发分析       │
│  execution_id  │
└───────┬─────────┘
        │
        ▼
┌──────────────────────────┐
│ 1. 获取执行数据        │
│    - 失败测试列表     │
│    - 错误日志         │
│    - 历史执行         │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────────┐
│ 2. 数据清洗与格式化   │
│    - 提取堆栈 trace    │
│    - 提取错误信息     │
│    - 提取上下文       │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────────┐
│ 3. 构建 Prompt       │
│    - 系统提示词      │
│    - 上下文数据      │
│    - 输出格式要求    │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────────┐
│ 4. 调用 LLM API       │
│    - 选择提供商       │
│    - 发送请求        │
│    - 处理响应        │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────────┐
│ 5. 解析 AI 响应      │
│    - 提取根因分析    │
│    - 提取修复建议    │
│    - 置信度评分      │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────────┐
│ 6. 查找相似失败       │
│    - 向量相似度搜索   │
│    - 关联案例       │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────────┐
│ 7. 保存洞察结果      │
│    ai_insights       │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────────┐
│ 8. 返回分析结果        │
│    - root_cause      │
│    - suggestion       │
│    - confidence       │
└──────────────────────────┘
```

**Prompt 模板示例:**

```
你是一位资深的测试工程师，擅长分析测试失败原因。

请分析以下测试失败:

执行摘要:
{summary}

失败的测试:
{failed_tests}

错误日志:
{error_logs}

请按以下 JSON 格式返回分析结果:
{{
  "root_cause": "根本原因分析",
  "suggestion": "修复建议",
  "confidence": 0.85,
  "failure_category": "test_flaky|environment|test_code|infrastructure"
}}
```

---

### 3.5 审计日志写入流程

```
┌─────────────────┐
│   操作发生       │
│  (创建/更新/删除)│
└───────┬─────────┘
        │
        ▼
┌──────────────────────────┐
│ 1. 收集审计信息        │
│    - actor_id (操作者)│
│    - action (操作类型)│
│    - target_type       │
│    - target_id         │
│    - request/response │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────────┐
│ 2. 构建审计事件        │
│    audit_logs         │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────────┐
│ 3. 写入数据库         │
│    异步写入, 不阻塞   │
│    主业务流程          │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────────┐
│ 4. 事件投影 (可选)     │
│    - 治理概览更新      │
│    - 事件流更新        │
└──────────────────────────┘
```

**审计事件类型:**

| 模块 | 事件类型 | 说明 |
|-----|---------|------|
| 项目 | project.create | 创建项目 |
| | project.update | 更新项目 |
| | project.delete | 删除项目 |
| 执行 | execution.create | 创建执行 |
| | execution.start | 开始执行 |
| | execution.complete | 执行完成 |
| | execution.fail | 执行失败 |
| 门禁 | gate.evaluate | 评估门禁 |
| | gate.pass | 门禁通过 |
| | gate.fail | 门禁失败 |
| 通知 | notification.send | 发送通知 |
| | notification.fail | 通知失败 |
| | notification.fallback | 通知回退 |
| 设置 | settings.update | 更新设置 |
