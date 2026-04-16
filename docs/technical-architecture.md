# AIQAHub 技术架构设计

## 1. 技术栈概览

### 1.1 后端技术栈

| 层次 | 技术选型 | 版本 | 用途 |
|-----|---------|------|------|
| **Web 框架** | FastAPI | >= 0.115.0 | HTTP API 服务 |
| **ASGI 服务器** | Uvicorn | >= 0.30.0 | 异步 Web 服务器 |
| **数据验证** | Pydantic | >= 2.8.0 | 数据模型验证 |
| **配置管理** | Pydantic Settings | >= 2.4.0 | 环境配置 |
| **ORM** | SQLAlchemy | >= 2.0.0 | 数据库映射 |
| **迁移工具** | Alembic | >= 1.13.0 | 数据库版本管理 |
| **缓存** | Redis | >= 5.0.0 | 缓存与会话存储 |
| **任务队列** | Celery | >= 5.4.0 | 异步任务处理 |
| **语言** | Python | >= 3.11 | 开发语言 |

### 1.2 前端技术栈

| 层次 | 技术选型 | 版本 | 用途 |
|-----|---------|------|------|
| **UI 框架** | React | ^18.3.1 | 前端框架 |
| **路由** | React Router | ^6.26.2 | 客户端路由 |
| **构建工具** | Vite | ^5.4.2 | 构建与开发服务器 |
| **类型系统** | TypeScript | ^5.5.4 | 静态类型检查 |
| **测试** | Vitest | ^2.1.9 | 单元测试 |
| **测试工具** | Testing Library | ^16.3.0 | React 组件测试 |

### 1.3 基础设施

| 组件 | 技术选型 | 用途 |
|-----|---------|------|
| **数据库** | SQLite (开发) / PostgreSQL (生产) | 主数据存储 |
| **缓存** | Redis | 缓存、会话、任务队列 Broker |
| **消息队列** | Redis (Celery Broker) | 异步任务队列 |
| **文件存储** | 本地文件系统 / S3 兼容 | Artifact 存储 |

---

## 2. 系统架构图

### 2.1 部署架构

```
                    ┌─────────────┐
                    │   客户端     │
                    │  (浏览器)    │
                    └──────┬──────┘
                           │ HTTPS
                           ▼
                    ┌─────────────┐
                    │   Nginx     │  (可选，生产环境)
                    │  反向代理    │
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │  Frontend   │ │   Backend   │ │   Static    │
    │   (React)   │ │  (FastAPI)  │ │   Assets    │
    └─────────────┘ └──────┬──────┘ └─────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │  Database   │ │    Redis    │ │  Celery     │
    │ (PostgreSQL)│ │   (Cache)   │ │   Workers   │
    └─────────────┘ └──────┬──────┘ └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  File Store │
                    │  (S3/Local) │
                    └─────────────┘
```

### 2.2 后端分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                        API 层                                 │
│  app/api/v1/routes/                                          │
│  - projects.py, suites.py, executions.py, reports.py        │
│  - gates.py, ai.py, assets.py, settings.py                  │
│  - governance.py, audit.py, connectors.py                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      服务层 (Services)                        │
│  app/services/                                                │
│  - project_service.py, suite_service.py                      │
│  - report_service.py, asset_service.py                       │
│  - environment_service.py, auth_service.py                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      CRUD 层 (Repository)                     │
│  app/crud/                                                    │
│  - base.py (基础 CRUD)                                       │
│  - project.py, suite.py, execution.py                        │
│  - artifact.py, quality_rule.py, asset.py                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      模型层 (Models)                          │
│  app/models/                                                  │
│  - project.py, suite.py, execution.py                        │
│  - report.py, quality_rule.py, ai_insight.py                 │
│  - asset.py, audit_log.py, user.py, role.py                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据库层                                  │
│  SQLite / PostgreSQL                                          │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 前端组件架构

```
┌─────────────────────────────────────────────────────────────┐
│                        页面层 (Pages)                         │
│  frontend/src/pages/                                          │
│  - DashboardPage.tsx                                          │
│  - ProjectsPage.tsx, ProjectDetailPage.tsx                   │
│  - SuitesPage.tsx, ExecutionsPage.tsx                        │
│  - ReportsPage.tsx, ReportDetailPage.tsx                     │
│  - GatesPage.tsx, AiPage.tsx, AssetsPage.tsx                │
│  - GovernancePage.tsx, SettingsPage.tsx                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      组件层 (Components)                       │
│  frontend/src/components/                                     │
│  - Shell.tsx (布局壳)                                         │
│  - Section.tsx, Highlight.tsx                                │
│  - QueryToolbar.tsx, PaginationControls.tsx                  │
│  - PlaywrightSummaryCard.tsx                                  │
│  - AiReplayComparison.tsx                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      基础设施层                                │
│  frontend/src/                                                │
│  - lib/api.ts (API 客户端)                                   │
│  - auth.tsx (认证)                                            │
│  - styles.css (样式)                                          │
│  - App.tsx (路由)                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 核心模块技术实现

### 3.1 执行编排引擎

**文件位置**: `app/orchestration/`

**核心组件**:
- `engine.py`: 编排引擎主体
- `state_machine.py`: 状态机实现
- `retry_policy.py`: 重试策略
- `timeout_policy.py`: 超时策略

**状态机设计**:
```python
class ExecutionState(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

# 允许的状态转换
TRANSITIONS = {
    ExecutionState.PENDING: [ExecutionState.QUEUED, ExecutionState.CANCELLED],
    ExecutionState.QUEUED: [ExecutionState.RUNNING, ExecutionState.CANCELLED],
    ExecutionState.RUNNING: [
        ExecutionState.COMPLETED,
        ExecutionState.FAILED,
        ExecutionState.TIMEOUT,
        ExecutionState.CANCELLED,
    ],
}
```

### 3.2 连接器框架

**文件位置**: `app/connectors/`

**基类设计**:
```python
class BaseConnector(ABC):
    @abstractmethod
    def validate_config(self, config: dict) -> bool:
        pass

    @abstractmethod
    async def execute(self, execution_id: str, config: dict) -> ExecutionResult:
        pass

    @abstractmethod
    async def poll_status(self, execution_id: str) -> ExecutionStatus:
        pass

    @abstractmethod
    async def fetch_artifacts(self, execution_id: str) -> List[Artifact]:
        pass
```

**现有连接器**:
- `jenkins/`: Jenkins CI 集成
- `playwright/`: Playwright 测试执行
- `llm/`: LLM AI 服务集成

### 3.3 通知系统

**文件位置**: `app/notifications/`

**策略路由流程**:
```
1. 事件触发 → 获取事件上下文 (event_type, project_id)
2. 查找匹配策略:
   a. 优先查找 project 级别策略
   b. 未找到则回退到 global 级别策略
   c. 仍未找到则使用 notification_default_channel
3. 应用过滤器 (filters)
4. 按优先级发送通知
5. 失败回退到次优通道
6. 记录审计事件
```

**策略数据结构**:
```json
{
  "scope_type": "project",
  "scope_id": "proj-123",
  "event_type": "execution.failed",
  "channels": ["dingtalk", "email"],
  "target": "@all",
  "filters": {
    "environment": "prod",
    "severity": "critical"
  }
}
```

### 3.4 治理中心

**文件位置**: `app/api/v1/routes/governance.py`

**事件投影设计**:
治理中心通过审计日志作为单一事实源，按需投影生成不同视图：

```
审计日志 (audit_logs)
  ├─→ 投影 → 治理概览 (governance/overview)
  ├─→ 投影 → 事件流 (governance/events)
  └─→ 投影 → 通知事件 (governance/events?type=notification)
```

**关键指标**:
- 活跃项目数
- 今日执行数
- 执行成功率
- 通知发送数/失败数
- 连接器健康状态

### 3.5 异步任务处理

**文件位置**: `app/workers/`

**Celery 任务**:
- `tasks.py`: 基础任务
- `report_tasks.py`: 报告解析任务
- `ai_tasks.py`: AI 分析任务

**任务流程**:
```
API 请求
  ↓
创建 Execution (PENDING)
  ↓
提交 Celery 任务
  ↓
Worker 接收任务
  ↓
更新状态 → QUEUED → RUNNING
  ↓
执行连接器
  ↓
收集 Artifacts
  ↓
解析报告
  ↓
评估门禁
  ↓
发送通知
  ↓
更新状态 → COMPLETED/FAILED
  ↓
写入审计日志
```

---

## 4. 数据模型设计

### 4.1 核心实体关系

```
Project (项目)
  ├── Suite (测试套件)
  │     └── Execution (执行)
  │           ├── ExecutionTask (执行任务)
  │           ├── ExecutionArtifact (产物)
  │           └── GateEvaluation (门禁评估)
  ├── QualityRule (质量规则)
  │     └── QualityRuleRevision (规则修订)
  ├── Asset (资产)
  │     └── AssetRevision (资产版本)
  └── AIInsight (AI 洞察)

User (用户)
  ├── Role (角色)
  │     └── UserRole (用户角色关联)
  └── AuditLog (审计日志)
```

### 4.2 关键表设计

详细的数据库设计请参考 [detailed-design.md](./detailed-design.md)，包含：

- 18 张核心表的完整字段定义
- 索引设计
- 数据库初始化 SQL
- 状态流转说明

**核心表概览**:

| 表名 | 说明 | 核心字段 |
|-----|------|---------|
| users | 用户表 | id, email, username, hashed_password |
| roles | 角色表 | id, name, permissions_json |
| user_roles | 用户角色关联 | user_id, role_id, project_id |
| projects | 项目表 | id, code, name, owner_id, status |
| test_suites | 测试套件表 | id, project_id, name, suite_type, source_ref |
| executions | 执行表 | id, project_id, suite_id, status, trigger_type |
| execution_tasks | 执行任务表 | execution_id, task_key, status |
| execution_artifacts | 执行产物表 | execution_id, artifact_type, storage_uri |
| quality_rules | 质量规则表 | project_id, name, rule_type, config_json |
| quality_rule_revisions | 规则修订表 | rule_id, revision_number, config_json |
| gate_evaluations | 门禁评估表 | execution_id, status, summary_json |
| assets | 资产表 | project_id, name, asset_type |
| asset_revisions | 资产版本表 | asset_id, revision_number, content |
| ai_insights | AI 洞察表 | execution_id, insight_type, content_json |
| audit_logs | 审计日志表 | actor_id, action, target_type, target_id |

---

## 5. API 设计规范

### 5.1 RESTful 设计原则

- 资源命名使用复数: `/api/v1/projects`
- 版本化 API: `/api/v1/`
- 使用标准 HTTP 方法: GET, POST, PUT, DELETE
- 使用标准状态码: 200, 201, 400, 404, 500

### 5.2 核心 API 端点

完整的 API 详细设计请参考 [detailed-design.md](./detailed-design.md)，包含：

- 通用响应格式规范
- 错误响应格式
- 标准状态码说明
- 7 大模块 API 详细文档
- 请求/响应示例

**API 模块概览**:

| 模块 | 主要端点 | 说明 |
|-----|---------|------|
| 项目 | `/api/v1/projects` | CRUD、列表查询 |
| 套件 | `/api/v1/suites` | 测试套件管理 |
| 执行 | `/api/v1/executions` | 创建、触发、查询、artifacts、timeline |
| 门禁 | `/api/v1/gates` | 规则管理、评估 |
| AI | `/api/v1/ai` | 分析、历史 |
| 治理 | `/api/v1/governance` | 概览、事件流 |
| 通知 | `/api/v1/notifications` | 测试发送 |

### 5.3 分页与过滤

**分页**:
```
GET /api/v1/executions?page=1&page_size=20
```

**过滤**:
```
GET /api/v1/executions?project_id=xxx&status=completed&started_after=2024-01-01
```

**排序**:
```
GET /api/v1/executions?sort_by=created_at&sort_order=desc
```

---

## 6. 安全设计

### 6.1 认证与授权

- **认证**: JWT Bearer Token
- **授权**: 基于角色的访问控制 (RBAC)
  - `admin`: 平台管理员
  - `owner`: 项目所有者
  - `member`: 项目成员
  - `viewer`: 只读访问

### 6.2 数据安全

- 敏感配置加密存储
- API 请求速率限制
- SQL 注入防护 (SQLAlchemy ORM)
- XSS 防护 (前端转义)
- CORS 配置

---

## 7. 监控与可观测性

### 7.1 日志

- 结构化日志 (JSON)
- 日志分级: DEBUG, INFO, WARNING, ERROR
- 请求追踪 ID 透传

### 7.2 指标

- API 响应时间
- 执行成功率/失败率
- 任务队列积压
- 数据库连接池

### 7.3  tracing

- OpenTelemetry 集成
- 端到端请求追踪

---

## 8. 核心业务流程

详细的业务流程设计请参考 [detailed-design.md](./detailed-design.md)，包含：

- 测试执行流程 (12 步完整流程)
- 通知策略路由流程
- 质量门禁评估流程
- AI 失败分析流程
- 审计日志写入流程

### 8.1 测试执行流程概览

```
创建执行 → 排队 → 运行 → 收集产物 → 解析报告
    → 评估门禁 → 发送通知 → 完成
```

### 8.2 执行状态机

```
created → queued → running → completed
                    ↓
              failed / timeout / cancelled
```

### 8.3 通知策略优先级

1. 项目级策略 (project scope)
2. 全局策略 (global scope)
3. 默认通道 (notification_default_channel)
