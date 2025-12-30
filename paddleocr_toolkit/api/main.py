#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI后端 - Web界面
v1.2.0新增 - REST API服务
"""

import asyncio
import os
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    HTTPException,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from paddleocr_toolkit.api.file_manager import router as file_router
from paddleocr_toolkit.api.websocket_manager import manager
from paddleocr_toolkit.core.ocr_engine import OCREngineManager
from paddleocr_toolkit.plugins.loader import PluginLoader

# 找到 web 目錄
WEB_DIR = Path(__file__).parent.parent.parent / "web"
STATIC_DIR = WEB_DIR  # 目前 index.html 直接在 web 根目錄

app = FastAPI(
    title="PaddleOCR Toolkit API",
    description="專業級 OCR 文件處理 API",
    version="3.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 掛載路由
app.include_router(file_router)

# 靜態檔案服務 (如果目錄存在)
if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR)), name="web")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 任務儲存
tasks = {}
results = {}

# 配置
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)
PLUGIN_DIR = Path("paddleocr_toolkit/plugins")

# 初始化插件載入器
plugin_loader = PluginLoader(str(PLUGIN_DIR))
plugin_loader.load_all_plugins()

# 圖片大小限制 (避免 OCR 記憶體不足)
MAX_IMAGE_SIDE = 2500  # 像素


def resize_image_if_needed(file_path: str, max_side: int = MAX_IMAGE_SIDE) -> str:
    """
    檢測並縮小大圖片以避免 OCR 記憶體問題

    Args:
        file_path: 圖片路徑
        max_side: 最大邊長（預設 2500px）

    Returns:
        處理後的圖片路徑（縮小後的新檔案或原檔案）
    """
    try:
        from PIL import Image

        with Image.open(file_path) as img:
            width, height = img.size
            max_dim = max(width, height)

            if max_dim <= max_side:
                print(f"圖片大小 {width}x{height} 在限制內，不需要縮小")
                return file_path

            # 計算縮放比例
            scale = max_side / max_dim
            new_width = int(width * scale)
            new_height = int(height * scale)

            print(f"圖片太大 ({width}x{height})，縮小為 {new_width}x{new_height}")

            # 縮小圖片
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 儲存到新檔案
            path = Path(file_path)
            new_path = path.parent / f"{path.stem}_resized{path.suffix}"
            resized_img.save(str(new_path), quality=95)

            print(f"縮小後圖片已儲存: {new_path}")
            return str(new_path)

    except Exception as e:
        print(f"縮小圖片時發生錯誤: {e}，使用原始圖片")
        return file_path


class OCRRequest(BaseModel):
    """OCR请求模型"""

    mode: str = "hybrid"
    dpi: int = 200
    lang: str = "ch"


class TaskResponse(BaseModel):
    """任务响应模型"""

    task_id: str
    status: str
    message: str


class OCRResult(BaseModel):
    """OCR结果模型"""

    task_id: str
    status: str
    progress: float
    results: Optional[Any] = None
    error: Optional[str] = None


from paddleocr_toolkit.core.ocr_cache import ocr_cache
from paddleocr_toolkit.processors.parallel_pdf_processor import ParallelPDFProcessor

# 初始化平行處理器
parallel_processor = ParallelPDFProcessor()


async def process_ocr_task(
    task_id: str,
    file_path: str,
    mode: str,
    gemini_key: str = None,
    claude_key: str = None,
):
    """
    非同步處理 OCR 任務
    """
    tasks[task_id] = {"status": "processing", "progress": 0}
    processed_path = str(Path(file_path))

    try:
        # ... (快取與處理邏輯)
        # 0. 檢查快取
        await manager.send_progress_update(task_id, 5, "processing", "檢查快取...")
        cached_result = ocr_cache.get(processed_path, mode)
        if cached_result:
            await manager.send_progress_update(task_id, 100, "completed", "快取命中")
            results[task_id] = {
                "status": "completed",
                "progress": 100,
                "results": cached_result,
            }
            tasks[task_id] = {"status": "completed", "progress": 100}
            await manager.send_completion(task_id, cached_result)
            return

        # 1. 預處理圖片
        actual_path = processed_path
        if processed_path.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp")):
            await manager.send_progress_update(task_id, 10, "processing", "預處理圖片...")
            actual_path = await asyncio.to_thread(
                resize_image_if_needed, processed_path
            )

        # 2. 執行預測
        ext = Path(processed_path).suffix.lower()
        if ext == ".pdf":
            # PDF 使用並行處理器
            await manager.send_progress_update(
                task_id, 30, "processing", "PDF 並行辨識中..."
            )
            ocr_result = await asyncio.to_thread(
                parallel_processor.process_pdf_parallel, actual_path, {"mode": "basic"}
            )
        else:
            # 標準單點辨識
            await manager.send_progress_update(task_id, 30, "processing", "正在辨識...")

            def run_ocr():
                eng = OCREngineManager(
                    mode=mode, device="cpu", plugin_loader=plugin_loader
                )
                eng.init_engine()
                res = eng.predict(actual_path)
                eng.close()
                return res

            ocr_result = await asyncio.to_thread(run_ocr)

        # 3. 處理與校正結果
        await manager.send_progress_update(task_id, 80, "processing", "處理辨識文本...")

        # 提取文字內容
        text_content = ""
        if isinstance(ocr_result, list):
            pages_texts = []
            for page in ocr_result:
                if isinstance(page, list):
                    # PaddleOCR 標準格式: [[[box], [text, score]], ...]
                    line_texts = []
                    for line in page:
                        if isinstance(line, (list, tuple)) and len(line) >= 2:
                            if isinstance(line[1], (list, tuple)) and len(line[1]) >= 1:
                                line_texts.append(str(line[1][0]))
                        elif isinstance(line, dict):
                            # PaddleX 字典格式 (在列表內)
                            if "rec_texts" in line:
                                line_texts.extend([str(t) for t in line["rec_texts"]])
                            elif "text" in line:
                                line_texts.append(str(line["text"]))

                    pages_texts.append("\n".join(line_texts))

                elif isinstance(page, dict):
                    # PPStructure or newer PaddleOCR format
                    # 1. Check for 'res' (PPStructure standard)
                    if "res" in page and isinstance(page["res"], list):
                        page_text_parts = []
                        for region in page["res"]:
                            if isinstance(region, dict) and "text" in region:
                                page_text_parts.append(region["text"])
                            elif isinstance(region, str):
                                page_text_parts.append(region)
                        pages_texts.append("\n".join(page_text_parts))

                    # 2. Check for 'rec_texts' (PaddleOCR Direct Result / Parallel Processor)
                    elif "rec_texts" in page and isinstance(page["rec_texts"], list):
                        pages_texts.append(
                            "\n".join([str(t) for t in page["rec_texts"]])
                        )

                    # 3. Check for 'text' or 'rec_text' (Single String)
                    elif "text" in page:
                        pages_texts.append(str(page["text"]))
                    elif "rec_text" in page:
                        pages_texts.append(str(page["rec_text"]))

                    # Fallback
                    else:
                        pages_texts.append(str(page))
                else:
                    pages_texts.append(str(page))
            text_content = "\n\n".join(pages_texts)
        else:
            text_content = str(ocr_result)

        # 語義校正 (Gemini / Claude)
        current_text = text_content
        for provider in ["gemini", "claude"]:
            if provider in mode.lower():
                await manager.send_progress_update(
                    task_id, 90, "processing", f"{provider.capitalize()} 智慧勘誤中..."
                )
                try:
                    import os

                    from paddleocr_toolkit.llm.llm_client import create_llm_client

                    # 優先使用傳入的金鑰，次之使用環境變數
                    passed_key = gemini_key if provider == "gemini" else claude_key
                    api_key = passed_key or os.environ.get(
                        f"{provider.upper()}_API_KEY"
                    )

                    if api_key:
                        llm = create_llm_client(provider, api_key=api_key)
                        prompt = (
                            f"請修正以下 OCR 辨識結果中的錯誤，僅進行勘誤與排版修復：\n\n{text_content[:2500]}"
                        )
                        corrected = await asyncio.to_thread(llm.generate, prompt)
                        if corrected:
                            current_text = corrected
                except Exception as e:
                    print(f"{provider} 校正失敗: {e}")

        final_result = {
            "raw_result": current_text,
            "pages": len(ocr_result) if isinstance(ocr_result, list) else 1,
            "confidence": 0.95,
        }

        # 4. 存入快取與完成
        ocr_cache.set(processed_path, mode, final_result)
        results[task_id] = {
            "status": "completed",
            "progress": 100,
            "results": final_result,
        }
        tasks[task_id] = {"status": "completed", "progress": 100}
        await manager.send_completion(task_id, final_result)

    except Exception as e:
        error_msg = str(e)
        results[task_id] = {"status": "failed", "progress": 0, "error": error_msg}
        tasks[task_id] = {"status": "failed", "progress": 0}
        await manager.send_error(task_id, error_msg)
        print(f"Task {task_id} failed: {e}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """提供用戶友好的 Web 介面"""
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse(
        content="""
        <h1>PaddleOCR Toolkit API</h1>
        <p>Version: 1.2.0</p>
        <p><a href="/docs">API 文件</a></p>
    """
    )


@app.post("/api/ocr", response_model=TaskResponse)
async def upload_and_ocr(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,  # type: ignore[assignment]
    mode: str = "hybrid",
    gemini_key: str = Query(None),
    claude_key: str = Query(None),
):
    """
    上传文件并进行OCR处理

    Args:
        file: 上传的文件
        background_tasks: 后台任务
        mode: OCR模式

    Returns:
        任务ID和状态
    """
    # 生成任务ID
    task_id = str(uuid.uuid4())

    # 保存文件
    file_path = UPLOAD_DIR / f"{task_id}_{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 创建后台任务
    background_tasks.add_task(
        process_ocr_task, task_id, str(file_path), mode, gemini_key, claude_key
    )

    # 初始化任务状态
    tasks[task_id] = {"status": "queued", "progress": 0}

    return TaskResponse(task_id=task_id, status="queued", message="任务已创建，正在处理...")


@app.get("/api/tasks/{task_id}", response_model=OCRResult)
async def get_task_status(task_id: str):
    """
    获取任务状态

    Args:
        task_id: 任务ID

    Returns:
        任务状态和结果
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task_info = tasks[task_id]

    # 如果任务完成，返回结果
    if task_id in results:
        return OCRResult(**results[task_id], task_id=task_id)

    # 否则返回当前状态
    return OCRResult(
        task_id=task_id, status=task_info["status"], progress=task_info["progress"]
    )


@app.get("/api/results/{task_id}")
async def get_results(task_id: str):
    """
    获取OCR结果

    Args:
        task_id: 任务ID

    Returns:
        OCR结果
    """
    if task_id not in results:
        raise HTTPException(status_code=404, detail="结果不存在")

    return results[task_id]


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    if task_id in tasks:
        del tasks[task_id]
    if task_id in results:
        del results[task_id]

    return {"message": "任务已删除"}


class TranslationRequest(BaseModel):
    text: str
    target_lang: str = "en"
    provider: str = "ollama"
    api_key: Optional[str] = None
    model: Optional[str] = None


@app.get("/api/stats")
async def get_stats():
    """获取系统统计"""
    return {
        "total_tasks": len(tasks),
        "completed_tasks": sum(1 for t in tasks.values() if t["status"] == "completed"),
        "queued_tasks": sum(1 for t in tasks.values() if t["status"] == "queued"),
        "processing_tasks": sum(
            1 for t in tasks.values() if t["status"] == "processing"
        ),
    }


@app.get("/api/files")
async def list_files():
    """列出所有上傳的檔案"""
    files = []
    if UPLOAD_DIR.exists():
        for f in UPLOAD_DIR.iterdir():
            if f.is_file():
                stat = f.stat()
                files.append(
                    {
                        "name": f.name,
                        "size": stat.st_size,
                        "created_at": stat.st_ctime,
                        "modified_at": stat.st_mtime,
                    }
                )
    return files


@app.delete("/api/files/{filename}")
async def delete_file(filename: str):
    """刪除檔案"""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="檔案不存在")

    try:
        os.remove(file_path)
        return {"message": f"檔案 {filename} 已刪除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除失敗: {str(e)}")


@app.get("/api/files/{filename}/download")
async def download_file(filename: str):
    """下載檔案"""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="檔案不存在")

    return FileResponse(
        path=file_path, filename=filename, media_type="application/octet-stream"
    )


@app.get("/api/plugins")
async def list_plugins():
    """列出所有插件"""
    return plugin_loader.list_plugins()


@app.post("/api/export")
async def export_results(
    data: dict,  # 接收 { "text": "...", "format": "docx", "filename": "..." }
):
    """
    將辨識結果匯出為指定格式的檔案
    """
    text = data.get("text", "")
    out_format = data.get("format", "docx").lower()
    base_name = data.get("filename", "ocr_result")

    # 確保輸出目錄存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        if out_format == "docx":
            from docx import Document

            doc = Document()
            doc.add_heading("OCR 辨識結果報告", 0)
            doc.add_paragraph(text)
            out_file = OUTPUT_DIR / f"{base_name}_{int(time.time())}.docx"
            doc.save(str(out_file))

        elif out_format == "xlsx":
            from openpyxl import Workbook

            wb = Workbook()
            ws = wb.active
            ws.title = "OCR Result"
            # 按行分割內容寫入 Excel
            lines = text.split("\n")
            for idx, line in enumerate(lines):
                ws.cell(row=idx + 1, column=1, value=line)
            out_file = OUTPUT_DIR / f"{base_name}_{int(time.time())}.xlsx"
            wb.save(str(out_file))

        elif out_format == "txt":
            # 新增純文字匯出
            out_file = OUTPUT_DIR / f"{base_name}_{int(time.time())}.txt"
            out_file.write_text(text, encoding="utf-8")

        else:
            return {"status": "error", "message": f"不支援的格式: {out_format}"}

        return {
            "status": "success",
            "download_url": f"/api/files/download/{out_file.name}?directory=output",
            "filename": out_file.name
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/export-text/{task_id}")
async def export_text(task_id: str):
    """
    匯出任務的 OCR 結果為純文字檔案
    
    Args:
        task_id: 任務 ID
    
    Returns:
        FileResponse: 可下載的文字檔案
    """
    if task_id not in results:
        raise HTTPException(status_code=404, detail="任務不存在")
    
    task_result = results[task_id]
    if task_result.get("status") != "completed":
        raise HTTPException(status_code=400, detail="任務尚未完成")
    
    # 獲取文字內容
    text_content = task_result.get("results", {}).get("raw_result", "")
    
    # 生成文字檔案
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"ocr_result_{task_id}_{int(time.time())}.txt"
    output_file.write_text(text_content, encoding="utf-8")
    
    return FileResponse(
        path=output_file,
        filename=f"ocr_result.txt",
        media_type="text/plain; charset=utf-8"
    )


@app.post("/api/translate")
async def translate_text(request: TranslationRequest):
    """
    使用 AI 翻譯文字
    
    Args:
        request: 翻譯請求物件
    
    Returns:
        翻譯後的文字
    """
    text = request.text
    target_lang = request.target_lang
    provider = request.provider
    api_key = request.api_key
    model = request.model
    
    try:
        from paddleocr_toolkit.llm.llm_client import create_llm_client
        
        # 設定提示詞
        lang_map = {
            "en": "English",
            "zh-TW": "Traditional Chinese (繁體中文)",
            "zh-CN": "Simplified Chinese (简体中文)",
            "ja": "Japanese (日本語)",
            "ko": "Korean (한국어)",
            "es": "Spanish",
            "fr": "French",
            "de": "German"
        }
        
        target_language = lang_map.get(target_lang, target_lang)
        prompt = f"""請將以下文字翻譯成 {target_language}。
只需要輸出翻譯結果，不要有任何額外說明。

原文：
{text}

翻譯："""
        
        # 創建 LLM 客戶端
        kwargs = {}
        if api_key:
            kwargs["api_key"] = api_key
        if model:
            kwargs["model"] = model
        elif provider == "ollama":
            kwargs["model"] = "qwen2.5:7b"
            kwargs["base_url"] = "http://localhost:11434"
        
        llm = create_llm_client(provider=provider, **kwargs)
        
        # 檢查服務是否可用
        if not llm.is_available():
            return {
                "status": "error",
                "message": f"{provider} 服務不可用，請確認已啟動相關服務"
            }
        
        # 生成翻譯
        translated = llm.generate(prompt, temperature=0.3, max_tokens=4096)
        
        if not translated:
            print(f"[WARNING] 翻譯結果為空")
            return {
                "status": "error",
                "message": "翻譯失敗，請重試"
            }
        
        print(f"[SUCCESS] 翻譯完成，長度: {len(translated)}")
        return {
            "status": "success",
            "translated_text": translated,
            "provider": provider,
            "target_lang": target_lang
        }
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[ERROR] 翻譯錯誤: {e}")
        print(error_detail)
        return {
            "status": "error",
            "message": f"翻譯失敗: {str(e)}"
        }


@app.post("/api/convert")
async def convert_format(
    task_id: str,
    target_format: str,  # docx, xlsx, pdf, md, txt
    include_metadata: bool = True
):
    """
    將 OCR 結果轉換為指定格式
    
    Args:
        task_id: 任務 ID
        target_format: 目標格式 (docx/xlsx/pdf/md/txt)
        include_metadata: 是否包含元數據（僅 Markdown）
    
    Returns:
        FileResponse: 可下載的轉換檔案
    """
    if task_id not in results:
        raise HTTPException(status_code=404, detail="任務不存在")
    
    task_result = results[task_id]
    if task_result.get("status") != "completed":
        raise HTTPException(status_code=400, detail="任務尚未完成")
    
    text_content = task_result.get("results", {}).get("raw_result", "")
    
    # 生成輸出檔案
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time())
    
    try:
        from paddleocr_toolkit.utils.format_converter import FormatConverter
        
        converter = FormatConverter()
        
        if target_format == "docx":
            output_file = OUTPUT_DIR / f"ocr_result_{task_id}_{timestamp}.docx"
            converter.text_to_docx(text_content, str(output_file))
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        
        elif target_format == "xlsx":
            output_file = OUTPUT_DIR / f"ocr_result_{task_id}_{timestamp}.xlsx"
            converter.text_to_xlsx(text_content, str(output_file))
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        elif target_format == "pdf":
            output_file = OUTPUT_DIR / f"ocr_result_{task_id}_{timestamp}.pdf"
            converter.text_to_pdf_searchable(text_content, str(output_file))
            media_type = "application/pdf"
        
        elif target_format == "md":
            output_file = OUTPUT_DIR / f"ocr_result_{task_id}_{timestamp}.md"
            metadata = None
            if include_metadata:
                metadata = {
                    "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "pages": task_result.get("results", {}).get("pages", 1),
                    "confidence": task_result.get("results", {}).get("confidence", 0.95)
                }
            converter.text_to_markdown(text_content, str(output_file), metadata)
            media_type = "text/markdown; charset=utf-8"
        
        else:  # txt (向後兼容)
            output_file = OUTPUT_DIR / f"ocr_result_{task_id}_{timestamp}.txt"
            output_file.write_text(text_content, encoding="utf-8")
            media_type = "text/plain; charset=utf-8"
        
        return FileResponse(
            path=output_file,
            filename=f"ocr_result.{target_format}",
            media_type=media_type
        )
    
    except Exception as e:
        print(f"格式轉換失敗: {e}")
        raise HTTPException(status_code=500, detail=f"轉換失敗: {str(e)}")


@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time task updates
    """
    await manager.connect(websocket, task_id)
    try:
        while True:
            # Keep connection alive and listen for client messages if needed
            # For now, we just push updates from server
            data = await websocket.receive_text()
            # Optional: handle client commands
            if data == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, task_id)


if __name__ == "__main__":
    import uvicorn

    print(
        """
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║     PaddleOCR Toolkit API Server                     ║
    ║     v3.3.0                                           ║
    ║                                                       ║
    ║     Dashboard: http://localhost:8000/                ║
    ║     Docs:      http://localhost:8000/docs            ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    
    啟動伺服器...
    """
    )
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
