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
- 启动即自动建表并写入 demo 数据

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
