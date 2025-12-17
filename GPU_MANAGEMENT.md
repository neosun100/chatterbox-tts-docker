# GPU 显存管理说明

## 设计原理

Chatterbox TTS 实现了智能 GPU 显存管理，通过 **懒加载 + 即用即卸** 策略最大化 GPU 利用率。

## 状态转换

```
未加载 ──首次请求(20-30s)──→ GPU ──任务完成(2s)──→ CPU ──新请求(2-5s)──→ GPU
  ↑                                                      ↓
  └────────────────────超时/手动释放(1s)─────────────────┘
```

## 三种状态

| 状态 | 显存占用 | 响应时间 | 说明 |
|------|----------|----------|------|
| GPU | ~2-4GB | 即时 | 模型在 GPU 上，可立即推理 |
| CPU | ~0 | 2-5s | 模型在内存中，需转移到 GPU |
| Unloaded | 0 | 20-30s | 需从磁盘/网络加载 |

## API 接口

### 查看状态
```bash
curl http://localhost:7866/gpu/status
```

返回：
```json
{
  "model_location": "gpu",
  "idle_time": 45,
  "idle_timeout": 60,
  "gpu_memory_mb": 2048.5
}
```

### 手动卸载到 CPU
```bash
curl -X POST http://localhost:7866/gpu/offload
```

### 完全释放
```bash
curl -X POST http://localhost:7866/gpu/release
```

### 设置超时
```bash
curl -X POST http://localhost:7866/gpu/timeout -d "timeout=300"
```

## 配置

通过环境变量配置：

```bash
# 空闲超时（秒）
GPU_IDLE_TIMEOUT=60

# 模型类型
MODEL_TYPE=turbo  # turbo, standard, multilingual
```

## 最佳实践

1. **生产环境**：设置较长的超时（300-600秒），减少加载次数
2. **共享 GPU**：设置较短的超时（30-60秒），及时释放资源
3. **批量处理**：处理完成后手动调用 offload

## 监控

GPU 管理器会自动：
- 每 30 秒检查空闲状态
- 超时后自动卸载到 CPU
- 记录所有状态变化到日志

查看日志：
```bash
docker logs -f chatterbox-tts
```
