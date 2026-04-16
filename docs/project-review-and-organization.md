# AIQAHub 项目 Review 与整理

**日期**: 2026-04-16
**状态**: 质量管控增强完成，待 Review

---

## 一、项目变更概述

基于用户最新定位要求："强化质量管控，弱化测试管理（测试用例、测试计划、测试执行在 devops 已包含），先建立初步的质量门禁流程和规则"，本次变更完成了 AIQAHub 从"测试管理平台"到"质量管控平台"的定位调整。

---

## 二、新增文件清单

### 2.1 数据库模型层 (Models)

| 文件 | 说明 | 包含表 |
|-----|------|--------|
| `app/models/document.py` | 文档相关模型 | `documents`, `document_versions` |
| `app/models/review.py` | 评审相关模型 | `review_tasks`, `review_comments`, `review_checklists`, `review_scores` |
| `app/models/coverage.py` | 覆盖率相关模型 | `coverage_snapshots`, `coverage_metrics` |

### 2.2 Pydantic Schema 层

| 文件 | 说明 |
|-----|------|
| `app/schemas/document.py` | 文档、评审、覆盖率的完整 Schema 定义 |

### 2.3 CRUD 数据访问层

| 文件 | 说明 |
|-----|------|
| `app/crud/document.py` | DocumentRepository, DocumentVersionRepository |
| `app/crud/review.py` | ReviewTaskRepository, ReviewCommentRepository, ReviewChecklistRepository, ReviewScoreRepository |
| `app/crud/coverage.py` | CoverageSnapshotRepository, CoverageMetricRepository |

### 2.4 Service 业务逻辑层

| 文件 | 说明 |
|-----|------|
| `app/services/document_service.py` | DocumentService, ReviewService, CoverageService |

### 2.5 API 路由层

| 文件 | 说明 |
|-----|------|
| `app/api/v1/routes/documents.py` | 文档审查模块 API |
| `app/api/v1/routes/coverage.py` | 覆盖率分析模块 API |

### 2.6 数据库迁移

| 文件 | 说明 |
|-----|------|
| `alembic/versions/d8891057ed31_add_document_review_and_coverage_tables.py` | 新增 8 张表的完整迁移 |

### 2.7 文档

| 文件 | 说明 |
|-----|------|
| `docs/quality-control-enhancements-summary.md` | 质量管控增强总结 |
| `docs/project-review-and-organization.md` | 本文档 |

---

## 三、修改文件清单

| 文件 | 修改内容 |
|-----|---------|
| `docs/product-architecture.md` | 重新定位为质量管控平台，更新功能架构 |
| `docs/product-roadmap.md` | 重新规划 Phase 1-3 路线图 |
| `app/models/__init__.py` | 导出新模型 |
| `app/schemas/gate.py` | 增强质量门禁 Schema，新增规则类型和模板 |
| `app/api/v1/router.py` | 集成文档和覆盖率路由 |
| `alembic/env.py` | 导入新模型用于迁移 |

---

## 四、新增 API 端点一览

### 4.1 文档管理 API (`/api/v1/documents`)

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | `/` | 列出项目文档 |
| GET | `/{doc_id}` | 获取文档详情 |
| POST | `/` | 创建文档 |
| PUT | `/{doc_id}` | 更新文档 |
| GET | `/{doc_id}/versions` | 列出文档版本 |

### 4.2 评审任务 API (`/api/v1/documents`)

| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | `/{doc_id}/review-tasks` | 创建评审任务 |
| PUT | `/review-tasks/{task_id}` | 更新评审任务 |
| POST | `/review-tasks/{task_id}/comments` | 创建评审评论 |
| PUT | `/review-comments/{comment_id}` | 更新评审评论 |
| POST | `/review-tasks/{task_id}/checklist` | 创建检查清单项 |
| PUT | `/review-checklist/{checklist_id}` | 更新检查清单项 |
| POST | `/review-tasks/{task_id}/scores` | 创建评审评分 |

### 4.3 覆盖率 API (`/api/v1/coverage`)

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | `/snapshots` | 列出覆盖率快照 |
| GET | `/snapshots/{snapshot_id}` | 获取快照详情 |
| POST | `/snapshots` | 创建覆盖率快照 |
| GET | `/snapshots/{snapshot_id}/metrics` | 列出覆盖率指标 |
| POST | `/snapshots/{snapshot_id}/metrics` | 创建覆盖率指标 |

---

## 五、新增数据库表一览

### 5.1 文档模块 (4 张表)

| 表名 | 说明 | 关键字段 |
|-----|------|---------|
| `documents` | 文档主表 | id, project_id, title, doc_type, status, content_json |
| `document_versions` | 文档版本 | id, document_id, version, content_json |
| `review_tasks` | 评审任务 | id, document_id, status, review_type, priority, assignee_ids |
| `review_comments` | 评审评论 | id, review_task_id, comment_type, status, severity, content |
| `review_checklists` | 评审检查清单 | id, review_task_id, item_key, status, sort_order |
| `review_scores` | 评审评分 | id, review_task_id, dimension, score, weight, is_ai |

### 5.2 覆盖率模块 (2 张表)

| 表名 | 说明 | 关键字段 |
|-----|------|---------|
| `coverage_snapshots` | 覆盖率快照 | id, project_id, commit_sha, branch, tool_name, summary_json |
| `coverage_metrics` | 覆盖率指标 | id, snapshot_id, metric_type, covered, total, percentage |

---

## 六、质量门禁规则类型扩展

### 6.1 新增规则类型

| 规则类型 | 说明 | 配置示例 |
|---------|------|---------|
| `doc_review` | 文档评审状态检查 | `{"required_status": "APPROVED"}` |
| `doc_score` | 文档质量评分检查 | `{"min_score": 80, "score_dimension": "overall"}` |
| `coverage` | 覆盖率阈值检查 | `{"min_coverage": 80, "metric_type": "line"}` |
| `coverage_delta` | 覆盖率变化检查 | `{"max_drop": 2, "metric_type": "line"}` |

### 6.2 现有规则类型

| 规则类型 | 说明 |
|---------|------|
| `success_rate` | 测试通过率检查 |
| `task_count` | 任务数量检查 |
| `critical_tasks` | 关键任务检查 |

### 6.3 规则模板

新增 `RuleTemplate` 类和预定义模板：
- 文档审查类模板 (2 个)
- 覆盖率类模板 (3 个)
- 测试结果类模板 (3 个)

---

## 七、与 devops-platform 的集成边界

| 领域 | devops-platform | AIQAHub | 集成方式 |
|-----|----------------|---------|---------|
| 测试用例管理 | ✅ 核心 | ❌ 不涉及 | - |
| 测试计划 | ✅ 核心 | ❌ 不涉及 | - |
| 测试执行 | ✅ 核心 | ❌ 不涉及 | - |
| 文档管理 | ❌ 不涉及 | ✅ 核心 | - |
| 文档评审 | ❌ 不涉及 | ✅ 核心 | - |
| 测试结果聚合 | ⚠️ 基础 | ✅ 深度分析 | Webhook / API |
| 覆盖率分析 | ❌ 不涉及 | ✅ 核心 | 数据推送 |
| 质量门禁 | ⚠️ 简单规则 | ✅ 多维度管控 | PR / 发布集成 |
| AI 分析 | ❌ 不涉及 | ✅ 核心 | - |

### 集成流程

```
devops-platform 执行测试
    ↓
测试结果推送到 AIQAHub
    ↓
AIQAHub 进行深度分析 + 门禁评估
    ↓
结果回调 devops-platform
    ↓
devops-platform 执行流程阻断/放行
```

---

## 八、代码质量检查

### 8.1 导入测试

✅ 所有模块导入正常：
- `app.models` - OK
- `app.schemas` - OK
- `app.crud` - OK
- `app.services` - OK
- `app.api.v1.routes.documents` - OK
- `app.api.v1.routes.coverage` - OK

### 8.2 代码一致性

✅ 遵循现有代码风格：
- 使用 Mapped 类型注解
- 使用 Repository 模式
- 使用 Service 层封装业务逻辑
- 完整的审计日志集成
- RESTful API 设计

---

## 九、后续建议

### 9.1 立即可以继续

1. **运行数据库迁移**
   ```bash
   alembic upgrade head
   ```

2. **增强 GateService**
   - 支持 `doc_review` 规则类型
   - 支持 `doc_score` 规则类型
   - 支持 `coverage` 规则类型
   - 支持 `coverage_delta` 规则类型

3. **创建单元测试**
   - DocumentService 测试
   - ReviewService 测试
   - CoverageService 测试

4. **更新前端**
   - 文档管理页面
   - 文档评审页面
   - 覆盖率分析页面
   - 质量门禁规则编辑（新增类型）

5. **实现文档解析器**
   - Markdown 解析
   - OpenAPI/Swagger 解析
   - 自动提取检查项

### 9.2 Phase 1 完整功能

参考 `docs/product-roadmap.md` 中的 Phase 1 规划。

---

## 十、文件结构总览

```
AIQAHub/
├── app/
│   ├── models/
│   │   ├── document.py           [NEW]
│   │   ├── review.py             [NEW]
│   │   └── coverage.py           [NEW]
│   ├── schemas/
│   │   └── document.py           [NEW]
│   ├── crud/
│   │   ├── document.py           [NEW]
│   │   ├── review.py             [NEW]
│   │   └── coverage.py           [NEW]
│   ├── services/
│   │   └── document_service.py   [NEW]
│   └── api/v1/
│       ├── routes/
│       │   ├── documents.py      [NEW]
│       │   └── coverage.py       [NEW]
│       └── router.py             [MODIFIED]
├── alembic/
│   └── versions/
│       └── d8891057ed31_*.py    [NEW]
└── docs/
    ├── product-architecture.md   [MODIFIED]
    ├── product-roadmap.md        [MODIFIED]
    ├── quality-control-enhancements-summary.md  [NEW]
    └── project-review-and-organization.md         [NEW]
```

---

## 十一、总结

本次变更成功完成了：

1. ✅ **产品定位重新调整** - 从测试管理平台调整为质量管控平台
2. ✅ **文档审查模块完整实现** - Model → Schema → CRUD → Service → API
3. ✅ **覆盖率分析模块完整实现** - Model → Schema → CRUD → Service → API
4. ✅ **质量门禁规则增强** - 新增文档和覆盖率相关规则类型
5. ✅ **数据库迁移就绪** - 8 张新表的完整迁移脚本
6. ✅ **文档完整更新** - 产品架构、路线图、总结文档

所有新增代码遵循现有代码风格，导入测试通过，可以进行下一步开发。
