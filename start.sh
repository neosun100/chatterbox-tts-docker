#!/bin/bash
set -e

echo "=========================================="
echo "  Chatterbox TTS Docker Launcher"
echo "=========================================="

# 检查 nvidia-docker
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ nvidia-smi not found. Please install NVIDIA drivers."
    exit 1
fi

# 自动选择显存占用最少的 GPU
echo "🔍 Detecting GPUs..."
GPU_ID=$(nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits | \
         sort -t',' -k2 -n | head -1 | cut -d',' -f1 | tr -d ' ')

if [ -z "$GPU_ID" ]; then
    echo "❌ No GPU detected"
    exit 1
fi

GPU_MEM=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $GPU_ID | tr -d ' ')
GPU_FREE=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i $GPU_ID | tr -d ' ')
echo "✅ Selected GPU $GPU_ID (${GPU_MEM}MB used, ${GPU_FREE}MB free)"

# 加载 .env 文件
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# 设置环境变量
export NVIDIA_VISIBLE_DEVICES=${GPU_ID}
export PORT=${PORT:-7866}
export GPU_IDLE_TIMEOUT=${GPU_IDLE_TIMEOUT:-60}
export MODEL_TYPE=${MODEL_TYPE:-turbo}

# 检查端口是否被占用
if ss -tlnp 2>/dev/null | grep -q ":${PORT} "; then
    echo "❌ Port ${PORT} is already in use"
    echo "   Please change PORT in .env file"
    exit 1
fi

echo ""
echo "📋 Configuration:"
echo "   GPU: $NVIDIA_VISIBLE_DEVICES"
echo "   Port: $PORT"
echo "   Model: $MODEL_TYPE"
echo "   Idle Timeout: ${GPU_IDLE_TIMEOUT}s"
echo ""

# 拉取最新镜像
echo "📥 Pulling latest image..."
docker pull neosun/chatterbox-tts:latest

# 停止旧容器
docker-compose down 2>/dev/null || true

# 启动
echo "🚀 Starting container..."
docker-compose up -d

echo ""
echo "=========================================="
echo "✅ Chatterbox TTS is running!"
echo ""
echo "🌐 Web UI:     http://0.0.0.0:${PORT}"
echo "📚 API Docs:   http://0.0.0.0:${PORT}/docs"
echo "❤️  Health:    http://0.0.0.0:${PORT}/health"
echo ""
echo "📝 Logs: docker logs -f chatterbox-tts"
echo "🛑 Stop: docker-compose down"
echo "=========================================="
