FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV HF_HOME=/app/.cache/huggingface

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3.11-dev python3-pip \
    ffmpeg libsndfile1 git curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && python -m pip install --upgrade pip setuptools wheel

WORKDIR /app

# 复制依赖文件
COPY pyproject.toml .
COPY src/ src/

# 安装 Python 依赖
RUN pip install -e .
RUN pip install fastapi uvicorn[standard] python-multipart fastmcp

# 预下载模型（all-in-one）
ARG HF_TOKEN
RUN python -c "import os; os.environ['HF_TOKEN']='${HF_TOKEN}'; from huggingface_hub import login; login(token='${HF_TOKEN}'); from chatterbox.tts_turbo import ChatterboxTurboTTS; ChatterboxTurboTTS.from_pretrained(device='cpu')" && \
    echo "✅ Turbo model downloaded"

# 复制应用代码 - 放在模型下载后避免缓存问题
COPY gpu_manager.py api.py mcp_server.py ./

EXPOSE 7866

ENV PORT=7866
ENV GPU_IDLE_TIMEOUT=60
ENV MODEL_TYPE=turbo

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["python", "api.py"]
