# -*- coding: utf-8 -*-
"""
OCR Router Tests - Expanded for full coverage
"""
import pytest
import asyncio
import os
import uuid
from unittest.mock import MagicMock, patch, Mock
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException
from starlette.websockets import WebSocketDisconnect
from pathlib import Path
from paddleocr_toolkit.api.routers import ocr

# Compatibility for AsyncMock in Python 3.7
try:
    from unittest.mock import AsyncMock
except ImportError:

    class AsyncMock(MagicMock):
        async def __call__(self, *args, **kwargs):
            return super(AsyncMock, self).__call__(*args, **kwargs)

        def __await__(self):
            return self().__await__()


class TestOCRRouter:
    @pytest.fixture(autouse=True)
    def setup_deps(self):
        """Setup dependencies for all tests in class"""
        ocr.tasks = {}
        ocr.results = {}
        ocr.ocr_cache = MagicMock()
        ocr.ocr_cache.get.return_value = None

        async def mock_connect(ws, tid):
            await ws.accept()

        ocr.manager = MagicMock()
        ocr.manager.connect = mock_connect

        ocr.manager.send_completion = AsyncMock()
        ocr.manager.send_progress_update = AsyncMock()
        ocr.manager.send_error = AsyncMock()
        ocr.manager.send_personal_message = AsyncMock()
        ocr.parallel_processor = MagicMock()
        ocr.plugin_loader = MagicMock()
        ocr.UPLOAD_DIR = Path("tmp_uploads_ocr")
        ocr.OUTPUT_DIR = Path("tmp_output_ocr")
        ocr.UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
        ocr.OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
        yield
        import shutil

        if ocr.UPLOAD_DIR.exists():
            shutil.rmtree(str(ocr.UPLOAD_DIR))
        if ocr.OUTPUT_DIR.exists():
            shutil.rmtree(str(ocr.OUTPUT_DIR))

    @pytest.fixture
    def client(self):
        """Create test client with ocr router"""
        app = FastAPI()
        app.include_router(ocr.router)
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_process_ocr_task_cache_hit(self):
        """Test process_ocr_task when result is cached"""
        task_id = "test_cache"
        file_path = "test.png"
        ocr.ocr_cache.get.return_value = {"raw_result": "cached"}
        await ocr.process_ocr_task(task_id, file_path, "basic")
        assert ocr.results[task_id]["status"] == "completed"

    def test_upload_and_ocr(self, client):
        """Test file upload endpoint"""
        with patch(
            "paddleocr_toolkit.api.routers.ocr.check_rate_limit", return_value=True
        ), patch("paddleocr_toolkit.api.routers.ocr.open", MagicMock()):
            response = client.post(
                "/api/ocr", files={"file": ("test.png", b"fake", "image/png")}
            )
            assert response.status_code == 200

    def test_rate_limit_failure(self, client):
        """Test rate limit 429"""
        with patch(
            "paddleocr_toolkit.api.routers.ocr.check_rate_limit", return_value=False
        ):
            response = client.post(
                "/api/ocr", files={"file": ("test.png", b"fake", "image/png")}
            )
            assert response.status_code == 429

    def test_update_result(self, client):
        """Test /api/results/{task_id}/update coverage 251-261"""
        task_id = "task_upd"
        # Setup results[task_id] with proper nesting
        ocr.results[task_id] = {"status": "completed", "results": {"raw_result": "old"}}
        response = client.post(f"/api/results/{task_id}/update", json={"text": "new"})
        assert response.json()["status"] == "success"
        assert ocr.results[task_id]["results"]["raw_result"] == "new"

    def test_export_exception_final(self, client):
        """Test export general exception handler via caught exception"""
        with patch("openpyxl.Workbook", side_effect=Exception("XLSX Fail")):
            response = client.post("/api/export", json={"text": "hi", "format": "xlsx"})
            assert response.json()["status"] == "error"

    def test_translate_exception(self, client):
        """Test translate exception branch 351"""
        with patch(
            "paddleocr_toolkit.api.routers.ocr.create_llm_client",
            side_effect=Exception("LLM Fail"),
        ):
            response = client.post(
                "/api/translate",
                json={"text": "hi", "target_lang": "en", "provider": "ollama"},
            )
            assert response.json()["status"] == "error"

    def test_missing_tasks_fixed(self, client):
        """Test coverage 358, 365"""
        response = client.post(
            "/api/convert", json={"task_id": "none", "target_format": "txt"}
        )
        assert response.status_code == 404
        response = client.get("/api/export-searchable-pdf/none")
        assert response.status_code == 404

    def test_websocket_manager_none_fixed(self, client):
        """Test line 392 fallback when manager is None with exception catch"""
        with patch("paddleocr_toolkit.api.routers.ocr.manager", None):
            with pytest.raises(WebSocketDisconnect) as exc:
                with client.websocket_connect("/ws/task1"):
                    pass
            assert exc.value.code == 1011

    @pytest.mark.asyncio
    async def test_process_ocr_task_llm_fixed(self):
        """Test process_ocr_task with LLM branches ensuring correct parsing"""
        task_id = "test_llm_fix"
        # Patch BOTH create_llm_client AND get_event_loop.run_in_executor to avoid async issues
        with patch(
            "paddleocr_toolkit.api.routers.ocr.OCREngineManager"
        ) as mock_eng_cls, patch(
            "paddleocr_toolkit.api.routers.ocr.create_llm_client"
        ) as mock_llm_cls, patch.dict(
            os.environ, {"GEMINI_API_KEY": "fake_key"}
        ):
            mock_eng = MagicMock()
            mock_eng.predict.return_value = [{"res": [{"text": "Original Text"}]}]
            mock_eng_cls.return_value = mock_eng

            mock_llm = MagicMock()
            mock_llm.generate.return_value = "Corrected Text"
            mock_llm_cls.return_value = mock_llm

            # Directly patch run_in_executor to return Corrected Text
            with patch(
                "asyncio.BaseEventLoop.run_in_executor", new_callable=AsyncMock
            ) as mock_executor:
                mock_executor.return_value = "Corrected Text"
                await ocr.process_ocr_task(task_id, "test_file.png", "hybrid-gemini")

            assert ocr.results[task_id]["results"]["raw_result"] == "Corrected Text"

    @pytest.mark.asyncio
    async def test_full_ocr_parsing_variants_omega(self):
        """Test line 140-164 coverage deeply"""
        task_id = "p1"
        with patch(
            "paddleocr_toolkit.api.routers.ocr.OCREngineManager"
        ) as mock_eng_cls:
            mock_eng = MagicMock()
            mock_eng_cls.return_value = mock_eng

            # 140: line is dict with rec_texts
            mock_eng.predict.return_value = [[{"rec_texts": ["t1"]}]]
            await ocr.process_ocr_task(task_id, "f.png", "basic")
            assert "t1" in ocr.results[task_id]["results"]["raw_result"]

            # 160: page is dict with rec_text
            mock_eng.predict.return_value = [{"rec_text": "t3"}]
            await ocr.process_ocr_task("p3", "f.png", "basic")
            assert "t3" in ocr.results["p3"]["results"]["raw_result"]
