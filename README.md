# AIQAHub

AI 驱动的智能质量管控平台。

## 核心价值

**AIQAHub** = AI 驱动的智能质量管控平台

一个统一的质量管控平面，提供文档质量审查、测试结果聚合、覆盖率分析和多维度质量门禁能力。

> **定位说明**: 测试用例管理、测试计划、测试执行等功能已在 devops-platform 中包含，AIQAHub 聚焦于质量管控核心能力。

### 四大核心价值主张

1. **统一质量管控平面** - 消除数据孤岛，一个平台查看所有质量数据
2. **文档质量审查** - PRD、技术文档、API 文档的自动化 + 人工评审
3. **AI 增强分析** - 秒级根因分析，给出修复建议
4. **多维度质量门禁** - 文档、测试、覆盖率多维度规则管控研发流程
5. **完整治理可见性** - 完整审计，实时监控

### 已实现核心模块

| 模块 | 状态 | 说明 |
|-----|------|------|
| 项目管理 | ✅ | 项目创建、编辑、列表、详情 |
| 文档审查 | ✅ | 文档管理、版本、评审任务、评论、评分 |
| 覆盖率分析 | ✅ | 覆盖率快照、多维度指标、趋势分析 |
| 报告聚合 | ✅ | 多格式解析（JUnit/Playwright）、数据聚合 |
| 质量门禁 | ✅ | 多维度规则定义、规则评估、结果判定 |
| AI 分析 | ✅ | 分析入口、Mock 提供商、可扩展 |
| 资产库 | ✅ | 资产版本管理、关联追踪 |
| 通知中心 | ✅ | 三通道支持、策略路由、审计追踪 |
| 治理中心 | ✅ | 概览仪表盘、事件流、通知可见性 |

### 已集成连接器

- ✅ **Jenkins** - CI 集成、Webhook 支持
- ✅ **Playwright** - 测试报告解析
- ✅ **JUnit** - 测试报告解析
- ✅ **LLM AI** - OpenAI/Anthropic/本地模型、Mock 支持

## 与 devops-platform 的协作

| 领域 | devops-platform | AIQAHub |
|-----|----------------|---------|
| 测试用例管理 | ✅ 核心 | ❌ 不涉及 |
| 测试计划 | ✅ 核心 | ❌ 不涉及 |
| 测试执行 | ✅ 核心 | ❌ 不涉及 |
| 文档管理 | ❌ 不涉及 | ✅ 核心 |
| 文档评审 | ❌ 不涉及 | ✅ 核心 |
| 测试结果聚合 | ⚠️ 基础 | ✅ 深度分析 |
| 覆盖率分析 | ❌ 不涉及 | ✅ 核心 |
| 质量门禁 | ⚠️ 简单规则 | ✅ 多维度管控 |
| AI 分析 | ❌ 不涉及 | ✅ 核心 |

## 目标

- 以质量管控为核心，统一文档审查、测试结果、覆盖率、门禁和 AI 分析
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
- [产品路线图](docs/product-roadmap.md) - 分阶段规划、里程碑、演进路线
- [质量管控增强总结](docs/quality-control-enhancements-summary.md) - 本次质量管控增强的详细总结
- [项目 Review 与整理](docs/project-review-and-organization.md) - 完整的项目 Review 文档
- [当前功能梳理](docs/current-feature-review.md) - 当前功能与定位对齐分析
- [部署指南](docs/deployment.md) - 本地开发、Docker、生产环境部署
- [架构与运行手册](docs/architecture-and-runbook.md) - 架构概览、运行时流程、API 摘要

## 数据库迁移

新增表的迁移脚本已创建，运行：

```bash
# 升级数据库
alembic upgrade head

# 查看当前版本
alembic current

# 降级（如需要）
alembic downgrade -1
```

## 下一步

### 立即可以使用的场景

1. **统一查看测试结果** - 在各 CI 系统运行测试，结果上传到 AIQAHub 统一查看
2. **文档质量审查** - 上传 PRD/技术文档/API 文档，发起评审流程
3. **覆盖率分析** - 上传覆盖率报告，查看趋势和缺口
4. **质量门禁把关** - 定义多维度质量规则（文档/测试/覆盖率），自动评估
5. **失败快速分析** - 测试执行失败，触发 AI 分析，查看根因和修复建议
6. **治理与审计** - 查看治理概览、事件流、通知发送情况、审计日志

### 后续开发方向

参考 [产品路线图](docs/product-roadmap.md) 中的 Phase 1-3 规划：
- Phase 1: 质量管控核心（文档审查、覆盖率分析、门禁增强、研发流程集成）
- Phase 2: AI 智能化（文档智能分析、失败根因分析、质量风险预测）
- Phase 3: 生态与规模化（插件市场、企业级特性、SaaS 化）
