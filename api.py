"""Chatterbox TTS API Server - FastAPI + WebSocket"""
import os
import io
import uuid
import time
import tempfile
import logging
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, Form, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import torch
import torchaudio as ta

from gpu_manager import gpu_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(tempfile.gettempdir()) / "chatterbox_uploads"
OUTPUT_DIR = Path(tempfile.gettempdir()) / "chatterbox_outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

MODEL_TYPE = os.getenv("MODEL_TYPE", "turbo")

def load_model():
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时预加载模型到 GPU
    gpu_manager.preload(load_model, "ChatterboxTTS")
    logger.info(f"Chatterbox TTS started, model={MODEL_TYPE}, resident mode")
    yield

app = FastAPI(title="Chatterbox TTS API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {"status": "healthy", "model_type": MODEL_TYPE}

@app.get("/gpu/status")
async def gpu_status():
    return gpu_manager.get_status()

@app.post("/gpu/offload")
async def gpu_offload():
    gpu_manager.force_offload()
    return {"status": "offloaded"}

@app.post("/gpu/release")
async def gpu_release():
    gpu_manager.force_release()
    return {"status": "released"}

@app.post("/api/tts")
async def tts(
    text: str = Form(...),
    audio_prompt: Optional[UploadFile] = File(None),
    temperature: float = Form(0.8),
    top_p: float = Form(0.95),
    top_k: int = Form(1000),
    repetition_penalty: float = Form(1.2),
    exaggeration: float = Form(0.0),
    cfg_weight: float = Form(0.0),
    language_id: str = Form("en"),
):
    try:
        audio_prompt_path = None
        if audio_prompt and audio_prompt.filename:
            audio_prompt_path = str(UPLOAD_DIR / f"{uuid.uuid4()}.wav")
            with open(audio_prompt_path, "wb") as f:
                f.write(await audio_prompt.read())
        
        params = {'temperature': temperature, 'top_p': top_p, 'repetition_penalty': repetition_penalty}
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
        
        model = gpu_manager.get_model(load_func=load_model, model_name="ChatterboxTTS")
        
        gen_start = time.time()
        wav = model.generate(text, **params)
        gen_time = time.time() - gen_start
        
        output_path = OUTPUT_DIR / f"{uuid.uuid4()}.wav"
        ta.save(str(output_path), wav, model.sr)
        
        if audio_prompt_path and os.path.exists(audio_prompt_path):
            os.remove(audio_prompt_path)
        
        return FileResponse(
            str(output_path), media_type="audio/wav", filename="output.wav",
            headers={"X-Generation-Time": f"{gen_time:.2f}"}
        )
    except Exception as e:
        logger.exception("TTS error")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tts/stream")
async def tts_stream(text: str = Form(...), temperature: float = Form(0.8)):
    try:
        model = gpu_manager.get_model(load_func=load_model, model_name="ChatterboxTTS")
        gen_start = time.time()
        wav = model.generate(text, temperature=temperature)
        gen_time = time.time() - gen_start
        
        buffer = io.BytesIO()
        ta.save(buffer, wav, model.sr, format="wav")
        buffer.seek(0)
        
        async def audio_generator():
            while chunk := buffer.read(8192):
                yield chunk
        
        return StreamingResponse(
            audio_generator(), media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=output.wav", "X-Generation-Time": f"{gen_time:.2f}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/tts")
async def websocket_tts(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            text = data.get("text", "")
            if not text:
                await websocket.send_json({"error": "text is required"})
                continue
            try:
                model = gpu_manager.get_model(load_func=load_model, model_name="ChatterboxTTS")
                gen_start = time.time()
                wav = model.generate(text, temperature=data.get("temperature", 0.8))
                gen_time = time.time() - gen_start
                
                import base64
                buffer = io.BytesIO()
                ta.save(buffer, wav, model.sr, format="wav")
                await websocket.send_json({
                    "status": "completed",
                    "audio": base64.b64encode(buffer.getvalue()).decode(),
                    "sample_rate": model.sr,
                    "generation_time": round(gen_time, 2)
                })
            except Exception as e:
                await websocket.send_json({"status": "error", "error": str(e)})
    except WebSocketDisconnect:
        pass

UI_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatterbox TTS</title>
    <style>
        :root { --bg: #0f172a; --card: #1e293b; --text: #e2e8f0; --primary: #6366f1; --border: #334155; --success: #22c55e; }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { text-align: center; margin-bottom: 20px; }
        .card { background: var(--card); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-size: 14px; color: #94a3b8; }
        input, textarea, select { width: 100%; padding: 10px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg); color: var(--text); }
        textarea { min-height: 100px; resize: vertical; }
        button { background: var(--primary); color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 16px; }
        button:hover { opacity: 0.9; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-danger { background: #dc2626; }
        .btn-warning { background: #d97706; }
        .tags { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
        .tag { background: #312e81; color: #a5b4fc; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 13px; }
        .tag:hover { background: #4338ca; }
        .params { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .gpu-status { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
        .status-info { display: flex; align-items: center; gap: 15px; }
        .status-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
        .status-gpu { background: #22c55e; }
        .status-cpu { background: #eab308; }
        .status-unloaded { background: #64748b; }
        .gen-time { background: var(--success); color: white; padding: 8px 16px; border-radius: 8px; font-weight: bold; display: none; }
        audio { width: 100%; margin-top: 15px; }
        .progress { height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; margin-top: 10px; display: none; }
        .progress-bar { height: 100%; background: var(--primary); width: 0; transition: width 0.3s; }
        .result-row { display: flex; align-items: center; gap: 15px; margin-top: 15px; flex-wrap: wrap; }
        .header { display: flex; justify-content: center; align-items: center; gap: 15px; margin-bottom: 20px; position: relative; }
        .header h1 { margin: 0; }
        .lang-switch { padding: 8px 12px; width: auto; position: absolute; right: 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ Chatterbox TTS</h1>
            <select class="lang-switch" id="langSelect" onchange="switchLang(this.value)">
                <option value="en">EN</option>
                <option value="zh-CN">中文</option>
                <option value="zh-TW">繁體</option>
                <option value="ja">日本語</option>
            </select>
        </div>
        <div class="card">
            <div class="gpu-status">
                <div class="status-info">
                    <span class="status-dot" id="statusDot"></span>
                    <span><span data-i18n="gpu_status">GPU:</span> <strong id="gpuStatus">-</strong></span>
                </div>
                <div>
                    <button class="btn-warning" onclick="offloadGPU()" data-i18n="offload">Offload to CPU</button>
                    <button class="btn-danger" onclick="releaseGPU()" data-i18n="release">Release All</button>
                </div>
            </div>
        </div>
        <div class="card">
            <div class="form-group">
                <label data-i18n="text_label">Text to synthesize</label>
                <textarea id="text">Oh, that's hilarious! [chuckle] Um anyway, we do have a new model in store.</textarea>
            </div>
            <div class="tags" id="eventTags"></div>
            <div class="form-group">
                <label data-i18n="ref_audio">Reference Audio (optional)</label>
                <input type="file" id="audioPrompt" accept="audio/*">
            </div>
        </div>
        <div class="card">
            <h3 data-i18n="params">Parameters</h3>
            <div class="params">
                <div class="form-group"><label>Temperature</label><input type="range" id="temperature" min="0.1" max="2" step="0.1" value="0.8" oninput="tempVal.textContent=this.value"><span id="tempVal">0.8</span></div>
                <div class="form-group"><label>Top P</label><input type="range" id="topP" min="0" max="1" step="0.05" value="0.95" oninput="topPVal.textContent=this.value"><span id="topPVal">0.95</span></div>
                <div class="form-group"><label>Top K</label><input type="range" id="topK" min="0" max="1000" step="50" value="1000" oninput="topKVal.textContent=this.value"><span id="topKVal">1000</span></div>
                <div class="form-group"><label>Repetition Penalty</label><input type="range" id="repPenalty" min="1" max="2" step="0.05" value="1.2" oninput="repVal.textContent=this.value"><span id="repVal">1.2</span></div>
            </div>
        </div>
        <div class="card">
            <button id="generateBtn" onclick="generate()" data-i18n="generate">Generate ⚡</button>
            <div class="progress" id="progress"><div class="progress-bar" id="progressBar"></div></div>
            <div class="result-row">
                <audio id="audioOutput" controls style="display:none; flex:1;"></audio>
                <div class="gen-time" id="genTime"></div>
            </div>
        </div>
    </div>
    <script>
        const i18n = {
            en: { gpu_status: "Model:", offload: "Offload to CPU", release: "Release All", text_label: "Text to synthesize", ref_audio: "Reference Audio (optional)", params: "Parameters", generate: "Generate ⚡", generating: "Generating...", gen_time: "Generation: " },
            "zh-CN": { gpu_status: "模型状态:", offload: "卸载到 CPU", release: "完全释放", text_label: "要合成的文本", ref_audio: "参考音频（可选）", params: "参数设置", generate: "生成 ⚡", generating: "生成中...", gen_time: "生成耗时: " },
            "zh-TW": { gpu_status: "模型狀態:", offload: "卸載到 CPU", release: "完全釋放", text_label: "要合成的文字", ref_audio: "參考音頻（可選）", params: "參數設定", generate: "生成 ⚡", generating: "生成中...", gen_time: "生成耗時: " },
            ja: { gpu_status: "モデル:", offload: "CPUへ退避", release: "完全解放", text_label: "合成するテキスト", ref_audio: "参照音声（任意）", params: "パラメータ", generate: "生成 ⚡", generating: "生成中...", gen_time: "生成時間: " }
        };
        const tags = ["[clear throat]", "[sigh]", "[cough]", "[gasp]", "[chuckle]", "[laugh]", "[sniff]", "[groan]", "[shush]"];
        let currentLang = 'en';
        
        function switchLang(lang) { currentLang = lang; localStorage.setItem('lang', lang); document.querySelectorAll('[data-i18n]').forEach(el => { const key = el.getAttribute('data-i18n'); if (i18n[lang]?.[key]) el.textContent = i18n[lang][key]; }); }
        function initTags() { const c = document.getElementById('eventTags'); tags.forEach(tag => { const el = document.createElement('span'); el.className = 'tag'; el.textContent = tag; el.onclick = () => { const t = document.getElementById('text'); t.value = t.value.slice(0, t.selectionStart) + ' ' + tag + ' ' + t.value.slice(t.selectionEnd); }; c.appendChild(el); }); }
        async function updateGPUStatus() { try { const r = await fetch('/gpu/status'); const d = await r.json(); document.getElementById('gpuStatus').textContent = `${d.model_location.toUpperCase()} (${d.gpu_memory_mb}/${d.gpu_total_mb} MB)`; document.getElementById('statusDot').className = 'status-dot status-' + d.model_location; } catch(e) {} }
        async function offloadGPU() { await fetch('/gpu/offload', {method: 'POST'}); updateGPUStatus(); }
        async function releaseGPU() { await fetch('/gpu/release', {method: 'POST'}); updateGPUStatus(); }
        
        async function generate() {
            const btn = document.getElementById('generateBtn'), progress = document.getElementById('progress'), progressBar = document.getElementById('progressBar');
            const audio = document.getElementById('audioOutput'), genTimeEl = document.getElementById('genTime');
            btn.disabled = true; progress.style.display = 'block'; progressBar.style.width = '10%';
            
            // 实时计时器
            const startTime = Date.now();
            genTimeEl.style.display = 'block';
            genTimeEl.style.background = '#d97706';
            const timer = setInterval(() => {
                const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
                genTimeEl.textContent = i18n[currentLang].generating + ' ' + elapsed + 's';
            }, 100);
            
            const formData = new FormData();
            formData.append('text', document.getElementById('text').value);
            formData.append('temperature', document.getElementById('temperature').value);
            formData.append('top_p', document.getElementById('topP').value);
            formData.append('top_k', document.getElementById('topK').value);
            formData.append('repetition_penalty', document.getElementById('repPenalty').value);
            const audioFile = document.getElementById('audioPrompt').files[0];
            if (audioFile) formData.append('audio_prompt', audioFile);
            
            try {
                progressBar.style.width = '50%';
                const res = await fetch('/api/tts', { method: 'POST', body: formData });
                clearInterval(timer);
                progressBar.style.width = '90%';
                if (res.ok) {
                    const blob = await res.blob();
                    audio.src = URL.createObjectURL(blob);
                    audio.style.display = 'block';
                    progressBar.style.width = '100%';
                    
                    const genTime = res.headers.get('X-Generation-Time');
                    if (genTime) {
                        genTimeEl.textContent = i18n[currentLang].gen_time + genTime + 's';
                        genTimeEl.style.background = '#22c55e';
                    }
                } else {
                    const err = await res.json();
                    alert('Error: ' + err.detail);
                    genTimeEl.style.display = 'none';
                }
            } catch(e) { clearInterval(timer); alert('Error: ' + e.message); genTimeEl.style.display = 'none'; }
            
            btn.disabled = false;
            setTimeout(() => { progress.style.display = 'none'; progressBar.style.width = '0'; }, 500);
            updateGPUStatus();
        }
        
        initTags(); updateGPUStatus(); setInterval(updateGPUStatus, 5000);
        const savedLang = localStorage.getItem('lang') || 'en'; currentLang = savedLang;
        document.getElementById('langSelect').value = savedLang; switchLang(savedLang);
    </script>
</body>
</html>'''

@app.get("/", response_class=HTMLResponse)
async def index():
    return UI_HTML

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 7866)))
