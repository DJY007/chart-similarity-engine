#!/bin/bash

set -e

echo "🚀 K线模式匹配工具启动脚本"
echo "================================"

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  .env 文件不存在，正在创建..."
    cp .env.example .env
    echo "✅ .env 已创建，请编辑并填入 API 密钥"
    echo "📝 编辑命令: nano .env"
    exit 1
fi

# 检查 Python 依赖
echo "📦 检查 Python 依赖..."
if ! pip show fastapi > /dev/null; then
    echo "📥 安装 Python 依赖..."
    pip install -r requirements.txt
fi

# 初始化数据库
if [ ! -f data/klines.db ]; then
    echo "📊 初始化历史数据（首次运行，需要几分钟）..."
    python scripts/init_data.py
fi

# 启动后端服务
echo "🔧 启动后端服务..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 启动前端服务
echo "🎨 启动前端服务..."
cd frontend
npm install > /dev/null 2>&1
npm run dev &
FRONTEND_PID=$!

cd ..

echo ""
echo "✨ 服务已启动！"
echo "🌐 Web 应用: http://localhost:5173"
echo "📡 API 服务: http://localhost:8000"
echo ""
echo "按 Ctrl+C 停止服务"

# 等待进程
wait $BACKEND_PID $FRONTEND_PID
