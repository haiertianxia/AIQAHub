# AIQAHub

AI 质量保障平台骨架。

## 核心价值

**AIQAHub** = AI 驱动的智能质量保障平台

一个统一的质量管控平面，将分散的测试工具、执行环境、报告数据聚合在一起，提供 AI 增强的分析能力。

### 四大核心价值主张

1. **统一质量管控平面** - 消除数据孤岛，一个平台查看所有质量数据
2. **AI 增强分析** - 秒级根因分析，给出修复建议
3. **灵活可扩展** - 连接器框架，易于集成新工具
4. **多维度治理可见性** - 完整审计，实时监控

### 已实现 MVP（9 大模块）

| 模块 | 状态 | 说明 |
|-----|------|------|
| 项目管理 | ✅ | 项目创建、编辑、列表、详情 |
| 测试套件 | ✅ | 套件注册、分类、元数据 |
| 执行编排 | ✅ | 执行触发、状态机、Celery 异步 |
| 报告聚合 | ✅ | 多格式解析（JUnit/Playwright）、数据聚合 |
| 质量门禁 | ✅ | 规则定义、规则评估、结果判定 |
| AI 分析 | ✅ | 分析入口、Mock 提供商、可扩展 |
| 资产库 | ✅ | 资产版本管理、关联追踪 |
| 通知中心 | ✅ | 三通道支持、策略路由、审计追踪 |
| 治理中心 | ✅ | 概览仪表盘、事件流、通知可见性 |

### 已集成连接器

- ✅ **Jenkins** - CI 集成、Webhook 支持
- ✅ **Playwright** - 测试执行、报告解析
- ✅ **LLM AI** - OpenAI/Anthropic/本地模型、Mock 支持

## 目标

- 统一项目、套件、执行、报告、门禁和 AI 分析
- 以模块化单体起步，后续可拆服务
- 前端入口位于 `frontend/`

## 现状

当前仓库已经具备可运行的 MVP：

- FastAPI 后端
- SQLite + SQLAlchemy 持久化
- React + Vite 前端
- 项目、套件、执行、报告、门禁、AI、资产、配置、审计页面
- 治理中心页面 `/governance`
- 治理中心内包含 `Notification Events` 分区，可查看通知发送、失败、回退和跳过
- 启动即自动建表并写入 demo 数据
- 通知系统支持 `email` / `dingtalk` / `wecom` 三通道
- 通知策略支持按环境保存，并支持 `global` / `project` 级别覆盖

## 技术栈

| 层次 | 技术选型 |
|-----|---------|
| 后端框架 | FastAPI (Python 3.11+) |
| 前端框架 | React 18 + TypeScript |
| 构建工具 | Vite |
| ORM | SQLAlchemy 2.0 |
| 数据库 | SQLite (开发) / PostgreSQL (生产) |
| 缓存/消息队列 | Redis |
| 异步任务 | Celery 5.4 |
| 测试框架 | pytest + Vitest |

### 测试覆盖

- 后端测试覆盖率: **91%**
- 前端测试: 4 个测试文件，6 个测试通过

## 通知

通知配置支持按环境保存，页面位于 `Settings`：

- `notification_default_channel`
- `notification_email_enabled`
- `notification_email_smtp_host`
- `notification_email_smtp_port`
- `notification_email_from`
- `notification_email_to`
- `notification_dingtalk_enabled`
- `notification_dingtalk_webhook_url`
- `notification_wecom_enabled`
- `notification_wecom_webhook_url`
- `notification_policies`（JSON 数组，支持 `scope_type`、`scope_id`、`event_type`、`channels`、`target`、`filters`）

通知测试接口：

- `POST /api/v1/notifications/test`

自动通知会在执行失败、执行超时和门禁 FAIL 时触发，并优先按当前 settings 中的通知策略路由：

1. 优先匹配 `project` 级别策略
2. 没有项目策略时回退到 `global` 默认策略
3. 若没有匹配策略，则回退到 `notification_default_channel`

通知发送会被记录为治理审计事件，并投影到治理中心的 `Notification Events` 分区。通知失败不会阻断执行或门禁结果，只会作为治理可见性信号展示。

测试通知时可在请求体中指定 `project_id` 和 `event_type`，以验证具体策略。

## 快速开始

### 方式 1: 本地开发（推荐）

使用一键启动脚本：

```bash
./scripts/dev.sh
```

或手动启动：

**后端：**

```bash
python3 -m pip install -e .
python3 -m app.main
```

**前端（新终端）：**

```bash
npm --prefix frontend install
npm --prefix frontend run dev
```

### 方式 2: Docker Compose

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 访问应用

| 服务 | 地址 |
|-----|------|
| 前端 (Docker) | http://localhost:3000 |
| 前端 (本地) | http://localhost:5173 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health |

## 测试

```bash
python3 -m pytest -q
python3 -m compileall app
npm --prefix frontend run build
```

## 文档

- [产品架构设计](docs/product-architecture.md) - 产品定位、用户画像、功能模块详解
- [技术架构设计](docs/technical-architecture.md) - 技术栈、系统架构、概要设计
- [详细设计](docs/detailed-design.md) - 数据库设计、API 设计、业务流程设计
- [核心价值梳理](docs/core-value.md) - 项目核心价值、已实现功能、与竞品差异
- [产品路线图](docs/product-roadmap.md) - 分阶段规划、里程碑、演进路线
- [实施计划与任务拆分](docs/implementation-plan.md) - Sprint 任务拆解、资源规划、风险控制
- [任务跟踪与执行计划](docs/task-tracking.md) - 当前任务看板、每日检查清单
- [部署指南](docs/deployment.md) - 本地开发、Docker、生产环境部署
- [架构与运行手册](docs/architecture-and-runbook.md) - 架构概览、运行时流程、API 摘要
- [执行进度](docs/execution-progress.md) - 当前执行进度、已完成工作、下一步计划

## 下一步

### 立即可以使用的场景

1. **统一查看测试结果** - 在各 CI 系统运行测试，结果上传到 AIQAHub 统一查看
2. **质量门禁把关** - 定义质量规则，执行完成自动评估，失败触发通知
3. **失败快速分析** - 测试执行失败，触发 AI 分析，查看根因和修复建议
4. **治理与审计** - 查看治理概览、事件流、通知发送情况、审计日志

### Phase 1: 核心能力增强（短期）

- ⏰ 定时执行调度
- 📊 报告对比与趋势
- 📈 测试覆盖率集成
- 🔔 通知模板管理
- 🔗 CI/CD 深度集成

详细路线图请参考 [产品路线图](docs/product-roadmap.md)。
