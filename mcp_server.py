"""Chatterbox TTS MCP Server"""
import os
import sys
import tempfile
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import FastMCP
import torch
import torchaudio as ta

from gpu_manager import gpu_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("chatterbox-tts")

MODEL_TYPE = os.getenv("MODEL_TYPE", "turbo")
OUTPUT_DIR = Path(tempfile.gettempdir()) / "chatterbox_mcp"
OUTPUT_DIR.mkdir(exist_ok=True)

def load_model():
    """加载 TTS 模型"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if MODEL_TYPE == "turbo":
        from chatterbox.tts_turbo import ChatterboxTurboTTS
        return ChatterboxTurboTTS.from_pretrained(device=device)
    elif MODEL_TYPE == "multilingual":
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        return ChatterboxMultilingualTTS.from_pretrained(device=device)
    else:
        from chatterbox.tts import ChatterboxTTS
        return ChatterboxTTS.from_pretrained(device=device)

# 启动监控
timeout = int(os.getenv('GPU_IDLE_TIMEOUT', 600))
gpu_manager.set_timeout(timeout)
gpu_manager.start_monitor()

@mcp.tool()
def tts_generate(
    text: str,
    output_path: str = None,
    audio_prompt_path: str = None,
    temperature: float = 0.8,
    top_p: float = 0.95,
    top_k: int = 1000,
    repetition_penalty: float = 1.2,
    exaggeration: float = 0.0,
    cfg_weight: float = 0.0,
    language_id: str = "en"
) -> dict:
    """
    文本转语音生成
    
    Args:
        text: 要合成的文本，支持 [laugh] [chuckle] [cough] 等标签
        output_path: 输出音频路径，不指定则自动生成
        audio_prompt_path: 参考音频路径（用于声音克隆）
        temperature: 采样温度 (0.1-2.0)
        top_p: Top-P 采样 (0-1)
        top_k: Top-K 采样 (0-1000)
        repetition_penalty: 重复惩罚 (1.0-2.0)
        exaggeration: 表现力 (0-1, 仅标准/多语言模型)
        cfg_weight: CFG 权重 (0-1, 仅标准/多语言模型)
        language_id: 语言代码 (仅多语言模型)
    
    Returns:
        包含 status 和 output_path 的字典
    """
    try:
        if not text:
            return {"status": "error", "error": "text is required"}
        
        # 构建参数
        params = {
            'temperature': temperature,
            'top_p': top_p,
            'repetition_penalty': repetition_penalty,
        }
        
        if MODEL_TYPE == "turbo":
            params['top_k'] = top_k
        else:
            params['exaggeration'] = exaggeration
            params['cfg_weight'] = cfg_weight
            params['min_p'] = 0.05
        
        if MODEL_TYPE == "multilingual":
            params['language_id'] = language_id
        
        if audio_prompt_path:
            params['audio_prompt_path'] = audio_prompt_path
        
        # 生成
        model = gpu_manager.get_model(load_func=load_model, model_name="ChatterboxTTS")
        wav = model.generate(text, **params)
        gpu_manager.force_offload()
        
        # 保存
        if not output_path:
            import uuid
            output_path = str(OUTPUT_DIR / f"{uuid.uuid4()}.wav")
        
        ta.save(output_path, wav, model.sr)
        
        return {
            "status": "success",
            "output_path": output_path,
            "sample_rate": model.sr,
            "model_type": MODEL_TYPE
        }
    
    except Exception as e:
        gpu_manager.force_offload()
        logger.exception("TTS generation error")
        return {"status": "error", "error": str(e)}

@mcp.tool()
def get_gpu_status() -> dict:
    """
    获取 GPU 状态
    
    Returns:
        GPU 状态信息，包括模型位置、显存占用、空闲时间
    """
    return gpu_manager.get_status()

@mcp.tool()
def offload_gpu() -> dict:
    """
    将模型从 GPU 卸载到 CPU，释放显存
    
    Returns:
        操作状态
    """
    gpu_manager.force_offload()
    return {"status": "offloaded", **gpu_manager.get_status()}

@mcp.tool()
def release_gpu() -> dict:
    """
    完全释放 GPU 资源，清空所有模型缓存
    
    Returns:
        操作状态
    """
    gpu_manager.force_release()
    return {"status": "released", **gpu_manager.get_status()}

@mcp.tool()
def set_gpu_timeout(timeout_seconds: int) -> dict:
    """
    设置 GPU 空闲超时时间
    
    Args:
        timeout_seconds: 超时秒数，超过此时间自动卸载到 CPU
    
    Returns:
        操作状态
    """
    gpu_manager.set_timeout(timeout_seconds)
    return {"status": "ok", "timeout": timeout_seconds}

@mcp.tool()
def get_supported_tags() -> dict:
    """
    获取支持的语音标签列表
    
    Returns:
        支持的标签列表
    """
    return {
        "tags": [
            "[clear throat]", "[sigh]", "[shush]", "[cough]", 
            "[groan]", "[sniff]", "[gasp]", "[chuckle]", "[laugh]"
        ],
        "description": "在文本中插入这些标签可以添加相应的语音效果"
    }

@mcp.tool()
def get_supported_languages() -> dict:
    """
    获取多语言模型支持的语言列表
    
    Returns:
        支持的语言代码和名称
    """
    return {
        "languages": {
            "ar": "Arabic", "da": "Danish", "de": "German", "el": "Greek",
            "en": "English", "es": "Spanish", "fi": "Finnish", "fr": "French",
            "he": "Hebrew", "hi": "Hindi", "it": "Italian", "ja": "Japanese",
            "ko": "Korean", "ms": "Malay", "nl": "Dutch", "no": "Norwegian",
            "pl": "Polish", "pt": "Portuguese", "ru": "Russian", "sv": "Swedish",
            "sw": "Swahili", "tr": "Turkish", "zh": "Chinese"
        },
        "note": "仅 multilingual 模型支持多语言"
    }

if __name__ == "__main__":
    mcp.run()
