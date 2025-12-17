[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

# ⚡ Chatterbox TTS Docker

[![Docker](https://img.shields.io/badge/Docker-neosun%2Fchatterbox--tts-blue?logo=docker)](https://hub.docker.com/r/neosun/chatterbox-tts)
[![Version](https://img.shields.io/badge/version-1.0.0-green)](https://github.com/neosun100/chatterbox-tts-docker/releases)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Resemble AI [Chatterbox TTS](https://github.com/resemble-ai/chatterbox) 的 All-in-One Docker 映像檔。支援 Web UI、REST API 和 WebSocket，內建 GPU 顯存管理。

![Screenshot](screenshot.png)

## ✨ 功能特色

- 🐳 **All-in-One 映像檔** - 模型預先下載，開箱即用
- 🎨 **Web UI** - 精美的多語言介面（EN/中文/繁體/日本語）
- 🔌 **REST API** - 簡潔的 HTTP 介面
- 🌊 **WebSocket** - 即時串流傳輸
- 🎭 **副語言標籤** - `[laugh]`、`[cough]`、`[sigh]` 等
- ⏱️ **即時計時** - 生成時間即時顯示
- 🎯 **GPU 常駐模式** - 模型常駐顯存，推理更快

## 🚀 快速開始

```bash
docker run -d --gpus all -p 7866:7866 neosun/chatterbox-tts:latest
```

瀏覽器開啟 http://localhost:7866

## 📦 安裝部署

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

## ⚙️ 設定說明

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `CUDA_VISIBLE_DEVICES` | `0` | GPU 裝置 ID |
| `PORT` | `7866` | 服務埠號 |
| `MODEL_TYPE` | `turbo` | 模型類型：`turbo`、`standard`、`multilingual` |

## 📡 API 介面

### 健康檢查
```bash
curl http://localhost:7866/health
```

### GPU 狀態
```bash
curl http://localhost:7866/gpu/status
```

### 文字轉語音
```bash
curl -X POST http://localhost:7866/api/tts \
  -F "text=你好，這是一個測試。" \
  -F "temperature=0.8" \
  -o output.wav
```

### 使用參考音訊
```bash
curl -X POST http://localhost:7866/api/tts \
  -F "text=你好世界" \
  -F "audio_prompt=@reference.wav" \
  -o output.wav
```

### GPU 管理
```bash
# 卸載到 CPU
curl -X POST http://localhost:7866/gpu/offload

# 完全釋放
curl -X POST http://localhost:7866/gpu/release
```

## 🎭 副語言標籤

為語音添加自然表情：

| 標籤 | 效果 |
|------|------|
| `[laugh]` | 大笑 |
| `[chuckle]` | 輕笑 |
| `[cough]` | 咳嗽 |
| `[sigh]` | 嘆氣 |
| `[gasp]` | 喘氣 |
| `[clear throat]` | 清嗓子 |
| `[sniff]` | 吸鼻子 |
| `[groan]` | 呻吟 |

範例：
```
"哦，太搞笑了！[chuckle] 嗯，總之，我們確實有一個新模型。"
```

## 🛠️ 技術棧

- **TTS 引擎**: Resemble AI [Chatterbox](https://github.com/resemble-ai/chatterbox)
- **後端**: FastAPI + Uvicorn
- **前端**: 原生 JS + i18n
- **容器**: NVIDIA CUDA 12.1 + Python 3.11

## 📁 專案結構

```
├── api.py              # FastAPI 服務 + Web UI
├── gpu_manager.py      # GPU 顯存管理
├── mcp_server.py       # MCP 伺服器（可選）
├── Dockerfile          # All-in-One 映像檔建置
├── docker-compose.yml  # Compose 設定
└── start.sh            # 容器入口腳本
```

## 🤝 參與貢獻

歡迎提交 Pull Request！

## 📄 開源協議

MIT License - 詳見 [LICENSE](LICENSE)

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/chatterbox-tts-docker&type=Date)](https://star-history.com/#neosun100/chatterbox-tts-docker)

## 📱 關注公眾號

![公眾號](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)
