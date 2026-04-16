#!/bin/bash

# AIQAHub 开发环境快速启动脚本
# 使用方法: ./scripts/dev.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  AIQAHub 开发环境启动脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查 Python
echo -e "${YELLOW}[1/6] 检查 Python 环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 Python3，请先安装 Python 3.11+${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
echo -e "${GREEN}  Python 版本: $PYTHON_VERSION${NC}"

# 检查并创建虚拟环境
echo ""
echo -e "${YELLOW}[2/6] 设置 Python 虚拟环境...${NC}"
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}  创建虚拟环境...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}  虚拟环境创建成功${NC}"
else
    echo -e "${GREEN}  虚拟环境已存在${NC}"
fi

# 激活虚拟环境并安装依赖
echo ""
echo -e "${YELLOW}[3/6] 安装 Python 依赖...${NC}"
source .venv/bin/activate
pip install -e .
echo -e "${GREEN}  Python 依赖安装完成${NC}"

# 检查 Node.js
echo ""
echo -e "${YELLOW}[4/6] 检查 Node.js 环境...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: 未找到 Node.js，请先安装 Node.js 18+${NC}"
    exit 1
fi
NODE_VERSION=$(node -v)
echo -e "${GREEN}  Node.js 版本: $NODE_VERSION${NC}"

# 安装前端依赖
echo ""
echo -e "${YELLOW}[5/6] 安装前端依赖...${NC}"
cd frontend
npm install
echo -e "${GREEN}  前端依赖安装完成${NC}"
cd ..

# 完成提示
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  开发环境设置完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}启动后端:${NC}"
echo -e "  source .venv/bin/activate && python3 -m app.main"
echo ""
echo -e "${YELLOW}启动前端 (新终端):${NC}"
echo -e "  cd frontend && npm run dev"
echo ""
echo -e "${YELLOW}或者使用 Docker 启动完整环境:${NC}"
echo -e "  docker-compose up"
echo ""
