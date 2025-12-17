# Chatterbox TTS MCP Guide

## 概述

Chatterbox TTS 提供 MCP (Model Context Protocol) 接口，允许 AI 助手直接调用 TTS 功能。

## 配置

将以下配置添加到你的 MCP 客户端配置文件：

```json
{
  "mcpServers": {
    "chatterbox-tts": {
      "command": "python",
      "args": ["/path/to/chatterbox/mcp_server.py"],
      "env": {
        "MODEL_TYPE": "turbo",
        "GPU_IDLE_TIMEOUT": "600"
      }
    }
  }
}
```

## 可用工具

### 1. tts_generate - 文本转语音

```python
result = await mcp.call_tool("tts_generate", {
    "text": "Hello, this is a test. [chuckle]",
    "output_path": "/tmp/output.wav",  # 可选
    "audio_prompt_path": "/path/to/ref.wav",  # 可选，声音克隆
    "temperature": 0.8,
    "top_p": 0.95,
    "top_k": 1000,
    "repetition_penalty": 1.2
})
```

**参数说明：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| text | str | 必填 | 要合成的文本 |
| output_path | str | 自动生成 | 输出音频路径 |
| audio_prompt_path | str | None | 参考音频（声音克隆） |
| temperature | float | 0.8 | 采样温度 |
| top_p | float | 0.95 | Top-P 采样 |
| top_k | int | 1000 | Top-K 采样 |
| repetition_penalty | float | 1.2 | 重复惩罚 |
| language_id | str | "en" | 语言代码（多语言模型） |

### 2. get_gpu_status - 获取 GPU 状态

```python
status = await mcp.call_tool("get_gpu_status", {})
# 返回: {"model_location": "gpu", "gpu_memory_mb": 2048, "idle_time": 30}
```

### 3. offload_gpu - 卸载到 CPU

```python
await mcp.call_tool("offload_gpu", {})
```

### 4. release_gpu - 完全释放

```python
await mcp.call_tool("release_gpu", {})
```

### 5. set_gpu_timeout - 设置超时

```python
await mcp.call_tool("set_gpu_timeout", {"timeout_seconds": 300})
```

### 6. get_supported_tags - 获取语音标签

```python
tags = await mcp.call_tool("get_supported_tags", {})
# 返回: {"tags": ["[laugh]", "[chuckle]", ...]}
```

### 7. get_supported_languages - 获取支持的语言

```python
langs = await mcp.call_tool("get_supported_languages", {})
```

## 语音标签

在文本中插入以下标签添加语音效果：

- `[laugh]` - 笑声
- `[chuckle]` - 轻笑
- `[cough]` - 咳嗽
- `[sigh]` - 叹气
- `[gasp]` - 喘气
- `[clear throat]` - 清嗓子
- `[sniff]` - 吸鼻子
- `[groan]` - 呻吟
- `[shush]` - 嘘声

## 示例

```python
# 生成带笑声的语音
result = await mcp.call_tool("tts_generate", {
    "text": "That's so funny! [laugh] Anyway, let me continue.",
    "temperature": 0.9
})

if result["status"] == "success":
    print(f"Audio saved to: {result['output_path']}")
```

## 与 API 的区别

| 特性 | MCP | REST API |
|------|-----|----------|
| 调用方式 | 工具调用 | HTTP 请求 |
| 适用场景 | AI 助手集成 | Web/移动应用 |
| 文件传输 | 本地路径 | 上传/下载 |
| 实时性 | 同步 | 同步 |

两者共享同一个 GPU 管理器，资源管理一致。
