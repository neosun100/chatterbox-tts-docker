[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

# ⚡ Chatterbox TTS Docker

[![Docker](https://img.shields.io/badge/Docker-neosun%2Fchatterbox--tts-blue?logo=docker)](https://hub.docker.com/r/neosun/chatterbox-tts)
[![Version](https://img.shields.io/badge/version-1.0.0-green)](https://github.com/neosun100/chatterbox-tts-docker/releases)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Resemble AI [Chatterbox TTS](https://github.com/resemble-ai/chatterbox) の All-in-One Docker イメージ。Web UI、REST API、WebSocket をサポートし、GPU メモリ管理機能を内蔵。

![Screenshot](screenshot.png)

## ✨ 機能

- 🐳 **All-in-One イメージ** - モデル事前ダウンロード済み、すぐに使用可能
- 🎨 **Web UI** - 美しい多言語インターフェース（EN/中文/繁體/日本語）
- 🔌 **REST API** - シンプルな HTTP エンドポイント
- 🌊 **WebSocket** - リアルタイムストリーミング対応
- 🎭 **パラ言語タグ** - `[laugh]`、`[cough]`、`[sigh]` など
- ⏱️ **リアルタイムタイマー** - 生成時間をリアルタイム表示
- 🎯 **GPU 常駐モード** - モデルを VRAM に常駐、高速推論

## 🚀 クイックスタート

```bash
docker run -d --gpus all -p 7866:7866 neosun/chatterbox-tts:latest
```

ブラウザで http://localhost:7866 を開く

## 📦 インストール

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

## ⚙️ 設定

| 変数 | デフォルト | 説明 |
|------|------------|------|
| `CUDA_VISIBLE_DEVICES` | `0` | GPU デバイス ID |
| `PORT` | `7866` | サーバーポート |
| `MODEL_TYPE` | `turbo` | モデル：`turbo`、`standard`、`multilingual` |

## 📡 API リファレンス

### ヘルスチェック
```bash
curl http://localhost:7866/health
```

### GPU ステータス
```bash
curl http://localhost:7866/gpu/status
```

### テキスト読み上げ
```bash
curl -X POST http://localhost:7866/api/tts \
  -F "text=こんにちは、テストです。" \
  -F "temperature=0.8" \
  -o output.wav
```

### 参照音声を使用
```bash
curl -X POST http://localhost:7866/api/tts \
  -F "text=こんにちは世界" \
  -F "audio_prompt=@reference.wav" \
  -o output.wav
```

### GPU 管理
```bash
# CPU へ退避
curl -X POST http://localhost:7866/gpu/offload

# 完全解放
curl -X POST http://localhost:7866/gpu/release
```

## 🎭 パラ言語タグ

音声に自然な表現を追加：

| タグ | 効果 |
|------|------|
| `[laugh]` | 笑い |
| `[chuckle]` | 軽い笑い |
| `[cough]` | 咳 |
| `[sigh]` | ため息 |
| `[gasp]` | 息を呑む |
| `[clear throat]` | 咳払い |
| `[sniff]` | 鼻をすする |
| `[groan]` | うめき声 |

例：
```
"ああ、面白い！[chuckle] えーと、とにかく、新しいモデルがあります。"
```

## 🛠️ 技術スタック

- **TTS エンジン**: Resemble AI [Chatterbox](https://github.com/resemble-ai/chatterbox)
- **バックエンド**: FastAPI + Uvicorn
- **フロントエンド**: Vanilla JS + i18n
- **コンテナ**: NVIDIA CUDA 12.1 + Python 3.11

## 📁 プロジェクト構成

```
├── api.py              # FastAPI サーバー + Web UI
├── gpu_manager.py      # GPU メモリ管理
├── mcp_server.py       # MCP サーバー（オプション）
├── Dockerfile          # All-in-One イメージビルド
├── docker-compose.yml  # Compose 設定
└── start.sh            # コンテナエントリーポイント
```

## 🤝 コントリビューション

Pull Request 歓迎！

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/chatterbox-tts-docker&type=Date)](https://star-history.com/#neosun100/chatterbox-tts-docker)

## 📱 フォローする

![WeChat](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)
