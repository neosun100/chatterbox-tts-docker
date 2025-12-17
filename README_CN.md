[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

# ⚡ Chatterbox TTS Docker

[![Docker](https://img.shields.io/badge/Docker-neosun%2Fchatterbox--tts-blue?logo=docker)](https://hub.docker.com/r/neosun/chatterbox-tts)
[![Version](https://img.shields.io/badge/version-1.0.0-green)](https://github.com/neosun100/chatterbox-tts-docker/releases)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Resemble AI [Chatterbox TTS](https://github.com/resemble-ai/chatterbox) 的 All-in-One Docker 镜像。支持 Web UI、REST API 和 WebSocket，内置 GPU 显存管理。

## ✨ 功能特性

- 🐳 **All-in-One 镜像** - 模型预下载，开箱即用
- 🎨 **Web UI** - 精美的多语言界面（EN/中文/繁體/日本語）
- 🔌 **REST API** - 简洁的 HTTP 接口
- 🌊 **WebSocket** - 实时流式传输
- 🎭 **副语言标签** - `[laugh]`、`[cough]`、`[sigh]` 等
- ⏱️ **实时计时** - 生成时间实时显示
- 🎯 **GPU 常驻模式** - 模型常驻显存，推理更快

## 🚀 快速开始

```bash
docker run -d --gpus all -p 7866:7866 neosun/chatterbox-tts:latest
```

浏览器打开 http://localhost:7866

## 📦 安装部署

### Docker Run

```bash
docker run -d \
  --name chatterbox-tts \
  --gpus '"device=0"' \
  -p 7866:7866 \
  -e CUDA_VISIBLE_DEVICES=0 \
  -e MODEL_TYPE=turbo \
  neosun/chatterbox-tts:latest
```

### Docker Compose

```yaml
services:
  chatterbox:
    image: neosun/chatterbox-tts:latest
    container_name: chatterbox-tts
    ports:
      - "7866:7866"
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - MODEL_TYPE=turbo
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ["0"]
              capabilities: [gpu]
```

```bash
docker compose up -d
```

## ⚙️ 配置说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CUDA_VISIBLE_DEVICES` | `0` | GPU 设备 ID |
| `PORT` | `7866` | 服务端口 |
| `MODEL_TYPE` | `turbo` | 模型类型：`turbo`、`standard`、`multilingual` |

## 📡 API 接口

### 健康检查
```bash
curl http://localhost:7866/health
```

### GPU 状态
```bash
curl http://localhost:7866/gpu/status
```

### 文本转语音
```bash
curl -X POST http://localhost:7866/api/tts \
  -F "text=你好，这是一个测试。" \
  -F "temperature=0.8" \
  -o output.wav
```

### 使用参考音频
```bash
curl -X POST http://localhost:7866/api/tts \
  -F "text=你好世界" \
  -F "audio_prompt=@reference.wav" \
  -o output.wav
```

### GPU 管理
```bash
# 卸载到 CPU
curl -X POST http://localhost:7866/gpu/offload

# 完全释放
curl -X POST http://localhost:7866/gpu/release
```

## 🎭 副语言标签

为语音添加自然表情：

| 标签 | 效果 |
|------|------|
| `[laugh]` | 大笑 |
| `[chuckle]` | 轻笑 |
| `[cough]` | 咳嗽 |
| `[sigh]` | 叹气 |
| `[gasp]` | 喘气 |
| `[clear throat]` | 清嗓子 |
| `[sniff]` | 吸鼻子 |
| `[groan]` | 呻吟 |

示例：
```
"哦，太搞笑了！[chuckle] 嗯，总之，我们确实有一个新模型。"
```

## 🛠️ 技术栈

- **TTS 引擎**: Resemble AI [Chatterbox](https://github.com/resemble-ai/chatterbox)
- **后端**: FastAPI + Uvicorn
- **前端**: 原生 JS + i18n
- **容器**: NVIDIA CUDA 12.1 + Python 3.11

## 📁 项目结构

```
├── api.py              # FastAPI 服务 + Web UI
├── gpu_manager.py      # GPU 显存管理
├── mcp_server.py       # MCP 服务器（可选）
├── Dockerfile          # All-in-One 镜像构建
├── docker-compose.yml  # Compose 配置
└── start.sh            # 容器入口脚本
```

## 🤝 参与贡献

欢迎提交 Pull Request！

## 📄 开源协议

MIT License - 详见 [LICENSE](LICENSE)

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/chatterbox-tts-docker&type=Date)](https://star-history.com/#neosun100/chatterbox-tts-docker)

## 📱 关注公众号

![公众号](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)
