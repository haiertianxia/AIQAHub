# AIQAHub

AI 质量保障平台骨架。

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
- 启动即自动建表并写入 demo 数据
- 通知系统支持 `email` / `dingtalk` / `wecom` 三通道
- 通知策略支持按环境保存，并支持 `global` / `project` 级别覆盖

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

测试通知时可在请求体中指定 `project_id` 和 `event_type`，以验证具体策略。

## 启动

后端：

```bash
python3 -m pip install -e .
python3 -m app.main
```

前端：

```bash
npm --prefix frontend install
npm --prefix frontend run dev
```

## 测试

```bash
python3 -m pytest -q
python3 -m compileall app
npm --prefix frontend run build
```

## 文档

- [架构与运行手册](docs/architecture-and-runbook.md)
