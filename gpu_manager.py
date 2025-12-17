"""GPU Resource Manager - 常驻显存模式"""
import threading
import time
import gc
import logging
import torch

logger = logging.getLogger(__name__)

class GPUResourceManager:
    """GPU 显存管理器 - 模型常驻，仅手动卸载"""
    
    def __init__(self):
        self.model = None
        self.model_on_cpu = None
        self.lock = threading.Lock()
        self._load_func = None
        self._model_name = "model"
    
    def preload(self, load_func, model_name: str = "model"):
        """启动时预加载模型到 GPU"""
        with self.lock:
            self._load_func = load_func
            self._model_name = model_name
            if self.model is None:
                logger.info(f"Preloading {model_name} to GPU...")
                start = time.time()
                self.model = load_func()
                logger.info(f"Model loaded in {time.time()-start:.1f}s")
    
    def get_model(self, load_func=None, model_name: str = "model"):
        """获取模型（常驻 GPU）"""
        with self.lock:
            if load_func:
                self._load_func = load_func
                self._model_name = model_name
            
            if self.model is not None:
                return self.model
            
            # 从 CPU 恢复
            if self.model_on_cpu is not None:
                logger.info(f"Moving {self._model_name} from CPU to GPU...")
                start = time.time()
                self.model = self._move_model_to_device(self.model_on_cpu, "cuda")
                self.model_on_cpu = None
                logger.info(f"Moved to GPU in {time.time()-start:.1f}s")
                return self.model
            
            # 首次加载
            if self._load_func:
                logger.info(f"Loading {self._model_name}...")
                start = time.time()
                self.model = self._load_func()
                logger.info(f"Loaded in {time.time()-start:.1f}s")
                return self.model
            
            raise RuntimeError("No model loaded")
    
    def _move_model_to_device(self, model, device: str):
        """移动模型到指定设备"""
        if hasattr(model, 'to'):
            return model.to(device)
        for attr in ['t3', 's3gen', 've', 'conds']:
            if hasattr(model, attr) and getattr(model, attr) is not None:
                setattr(model, attr, getattr(model, attr).to(device))
        model.device = device
        return model
    
    def _clear_gpu_cache(self):
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
    
    def force_offload(self):
        """手动卸载到 CPU"""
        with self.lock:
            if self.model is not None:
                self.model_on_cpu = self._move_model_to_device(self.model, "cpu")
                self.model = None
                self._clear_gpu_cache()
                logger.info("Model offloaded to CPU")
    
    def force_release(self):
        """完全释放"""
        with self.lock:
            self.model = None
            self.model_on_cpu = None
            self._clear_gpu_cache()
            logger.info("All models released")
    
    def get_status(self) -> dict:
        with self.lock:
            location = "unloaded"
            if self.model is not None:
                location = "gpu"
            elif self.model_on_cpu is not None:
                location = "cpu"
            
            gpu_mem_used = gpu_mem_total = 0
            try:
                import subprocess
                out = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
                    text=True
                ).strip().split("\n")[0].split(", ")
                gpu_mem_used, gpu_mem_total = int(out[0]), int(out[1])
            except:
                pass
            return {"model_location": location, "gpu_memory_mb": gpu_mem_used, "gpu_total_mb": gpu_mem_total}

gpu_manager = GPUResourceManager()
