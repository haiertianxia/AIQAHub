# AIQAHub 部署指南

## 目录

- [本地开发环境](#本地开发环境)
- [Docker Compose 部署](#docker-compose-部署)
- [生产环境部署](#生产环境部署)
- [配置说明](#配置说明)
- [故障排查](#故障排查)

---

## 本地开发环境

### 快速启动（推荐）

使用一键启动脚本：

```bash
# 克隆项目
git clone <repository-url>
cd AIQAHub

# 运行快速启动脚本
./scripts/dev.sh
```

### 手动启动

#### 1. 后端设置

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
python3 -m pip install -e .

# 启动后端
python3 -m app.main
```

后端将在 `http://localhost:8000` 启动。

#### 2. 前端设置

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 `http://localhost:5173` 启动。

#### 3. 访问应用

打开浏览器访问：
- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

---

## Docker Compose 部署

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+

### 快速启动

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

### 服务说明

| 服务 | 端口 | 说明 |
|-----|------|------|
| frontend | 3000 | Nginx 托管的前端 |
| backend | 8000 | FastAPI 后端 |
| redis | 6379 | Redis 缓存和 Celery Broker |
| celery-worker | - | Celery 异步任务 Worker |

### 访问应用

- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 开发模式 Docker

如需在 Docker 中进行开发（支持热重载），使用以下配置：

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    volumes:
      - ./app:/app/app
    command: python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
    command: npm run dev
```

---

## 生产环境部署

### 1. 环境准备

#### 系统要求

- Linux (Ubuntu 20.04+ / Debian 11+ / CentOS 8+)
- 4 CPU 核心
- 8 GB RAM
- 50 GB 磁盘空间

#### 安装 Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo apt-get install docker-compose-plugin
```

### 2. 生产配置

创建生产环境配置文件 `.env.production`:

```env
# 应用配置
APP_NAME=AIQAHub
APP_VERSION=0.1.0
ENVIRONMENT=production

# 数据库配置
DATABASE_URL=postgresql://user:password@db:5432/aiqahub

# Redis 配置
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/1

# 安全配置
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI 配置
AI_PROVIDER=openai
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your-openai-api-key

# 日志配置
LOG_LEVEL=INFO

# 通知配置
NOTIFICATION_DEFAULT_CHANNEL=email
NOTIFICATION_EMAIL_ENABLED=true
NOTIFICATION_EMAIL_SMTP_HOST=smtp.example.com
NOTIFICATION_EMAIL_SMTP_PORT=587
```

### 3. 生产部署 Docker Compose

创建 `docker-compose.production.yml`:

```yaml
version: '3.8'

services:
  # PostgreSQL 数据库
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: aiqahub
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: aiqahub
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aiqahub"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Redis
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    restart: unless-stopped

  # Backend
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      - DATABASE_URL=postgresql://aiqahub:${DB_PASSWORD}@db:5432/aiqahub
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - SECRET_KEY=${SECRET_KEY}
      - LOG_LEVEL=INFO
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    restart: unless-stopped

  # Frontend
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    depends_on:
      - backend
    restart: unless-stopped

  # Nginx (作为反向代理)
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

  # Celery Worker
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile.backend
    command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql://aiqahub:${DB_PASSWORD}@db:5432/aiqahub
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # Celery Beat (定时任务)
  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.backend
    command: celery -A app.workers.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://aiqahub:${DB_PASSWORD}@db:5432/aiqahub
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 4. 部署步骤

```bash
# 1. 上传代码到服务器
scp -r AIQAHub user@server:/opt/

# 2. SSH 登录服务器
ssh user@server
cd /opt/AIQAHub

# 3. 创建生产环境配置
cp .env.example .env.production
# 编辑 .env.production，填入实际配置

# 4. 启动服务
docker-compose -f docker-compose.production.yml up -d

# 5. 查看服务状态
docker-compose -f docker-compose.production.yml ps

# 6. 查看日志
docker-compose -f docker-compose.production.yml logs -f
```

### 5. SSL/TLS 配置

使用 Let's Encrypt 免费证书：

```bash
# 安装 certbot
sudo apt-get install certbot

# 获取证书
sudo certbot certonly --standalone -d your-domain.com

# 证书位置
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem

# 更新 nginx 配置使用证书
```

---

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|-------|--------|------|
| APP_NAME | AIQAHub | 应用名称 |
| APP_VERSION | 0.1.0 | 应用版本 |
| ENVIRONMENT | development | 运行环境 |
| DATABASE_URL | sqlite:///./aiqahub.db | 数据库连接 URL |
| REDIS_URL | redis://localhost:6379/0 | Redis 连接 URL |
| CELERY_BROKER_URL | redis://localhost:6379/1 | Celery Broker URL |
| CELERY_RESULT_BACKEND | redis://localhost:6379/1 | Celery 结果后端 |
| SECRET_KEY | (随机生成) | JWT 签名密钥 |
| LOG_LEVEL | INFO | 日志级别 |
| AI_PROVIDER | mock | AI 提供商 (mock/openai/anthropic) |
| OPENAI_API_KEY | - | OpenAI API 密钥 |

### 数据库 URL 格式

**SQLite:**
```
sqlite:///./aiqahub.db
```

**PostgreSQL:**
```
postgresql://user:password@host:5432/database
```

**MySQL:**
```
mysql+pymysql://user:password@host:3306/database
```

---

## 故障排查

### 常见问题

#### 1. 后端无法启动

**检查日志:**
```bash
docker-compose logs backend
```

**常见原因:**
- 数据库连接失败：检查 `DATABASE_URL`
- Redis 连接失败：检查 `REDIS_URL`
- 端口被占用：检查 8000 端口是否被占用

#### 2. 前端无法访问后端

**检查:**
- CORS 配置：确认后端允许前端域名
- 网络连接：确认前端能访问后端地址
- 防火墙：检查防火墙规则

#### 3. Celery 任务不执行

**检查:**
```bash
# 查看 Worker 日志
docker-compose logs celery-worker

# 检查队列状态
celery -A app.workers.celery_app inspect active
```

#### 4. 数据库迁移问题

**使用 Alembic:**
```bash
# 创建迁移
alembic revision --autogenerate -m "description"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 健康检查端点

| 端点 | 说明 |
|-----|------|
| `/health` | 后端健康检查 |
| `/api/v1/projects` | 项目列表 API |
| `/docs` | Swagger API 文档 |

### 获取帮助

如遇问题，请：
1. 查看日志: `docker-compose logs`
2. 检查服务状态: `docker-compose ps`
3. 访问 API 文档: `/docs`
4. 提交 Issue 到项目仓库
