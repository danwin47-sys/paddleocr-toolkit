# -*- coding: utf-8 -*-
"""
Advanced tests for OCR Router to maximize coverage.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch
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


class TestOCRRouterAdvanced:
    @pytest.fixture(autouse=True)
    def setup(self):
        ocr.tasks = {}
        ocr.results = {}
        ocr.manager = MagicMock()
        ocr.manager.send_error = AsyncMock()
        ocr.manager.send_completion = AsyncMock()
        ocr.manager.send_progress_update = AsyncMock()

    @pytest.mark.asyncio
    async def test_process_ocr_task_exception_handling(self):
        """Test exception handling in process_ocr_task"""
        task_id = "error_task"

        # Patch OCREngineManager to raise exception
        with patch(
            "paddleocr_toolkit.api.routers.ocr.OCREngineManager",
            side_effect=Exception("Critical OCR Failure"),
        ):
            await ocr.process_ocr_task(task_id, "file.png", "basic")

            assert ocr.tasks[task_id]["status"] == "failed"
            assert "Critical OCR Failure" in ocr.results[task_id]["error"]
            ocr.manager.send_error.assert_called_with(task_id, "Critical OCR Failure")

    @pytest.mark.asyncio
    async def test_llm_correction_failure_handled(self):
        """Test LLM exception inside process_ocr_task does not crash task"""
        task_id = "llm_fail_task"

        with patch(
            "paddleocr_toolkit.api.routers.ocr.OCREngineManager"
        ) as mock_eng_cls, patch(
            "paddleocr_toolkit.api.routers.ocr.create_llm_client",
            side_effect=Exception("LLM Init Error"),
        ):
            mock_eng = MagicMock()
            mock_eng.predict.return_value = "OCR Text"
            mock_eng_cls.return_value = mock_eng

            # Using basic-gemini mode to trigger LLM block
            await ocr.process_ocr_task(
                task_id, "file.png", "basic-gemini", gemini_key="key"
            )

            # Task should still succeed, just without LLM correction
            assert ocr.tasks[task_id]["status"] == "completed"
            assert ocr.results[task_id]["results"]["raw_result"] == "OCR Text"

    @pytest.mark.asyncio
    async def test_parsing_complex_list_structure(self):
        """Test parsing logic for nested lists (lines 136-139)"""
        task_id = "list_parse"

        with patch(
            "paddleocr_toolkit.api.routers.ocr.OCREngineManager"
        ) as mock_eng_cls:
            mock_eng = MagicMock()
            # Construct: [ page [ line [ poly, [text, score] ] ] ]
            complex_output = [[[[0, 0], ["Text 1", 0.99]], [[0, 0], ["Text 2", 0.98]]]]
            mock_eng.predict.return_value = complex_output
            mock_eng_cls.return_value = mock_eng

            await ocr.process_ocr_task(task_id, "file.png", "basic")

            result_text = ocr.results[task_id]["results"]["raw_result"]
            assert "Text 1" in result_text
            assert "Text 2" in result_text

    @pytest.mark.asyncio
    async def test_parsing_structure_dict_variants(self):
        """Test parsing logic for structure dict variants (lines 147-154)"""
        task_id = "dict_parse"

        with patch(
            "paddleocr_toolkit.api.routers.ocr.OCREngineManager"
        ) as mock_eng_cls:
            mock_eng = MagicMock()
            # Construct: [ { "res": [ {"text": "Region1"}, "Region2" ] } ]
            structure_output = [{"res": [{"text": "Region1"}, "Region2"]}]
            mock_eng.predict.return_value = structure_output
            mock_eng_cls.return_value = mock_eng

            await ocr.process_ocr_task(task_id, "file.png", "structure")

            result_text = ocr.results[task_id]["results"]["raw_result"]
            assert "Region1" in result_text
            assert "Region2" in result_text

    @pytest.mark.asyncio
    async def test_translate_text_unavailable(self):
        """Test translation service unavailable"""
        req_mock = MagicMock()
        req_mock.text = "Hello"
        req_mock.target_lang = "zh-TW"
        req_mock.provider = "ollama"
        req_mock.api_key = None
        req_mock.model = None

        with patch(
            "paddleocr_toolkit.api.routers.ocr.create_llm_client"
        ) as mock_llm_cls:
            mock_llm = MagicMock()
            mock_llm.is_available.return_value = False
            mock_llm_cls.return_value = mock_llm

            result = await ocr.translate_text(req_mock)
            assert result["status"] == "error"
            assert "服務不可用" in result["message"]

    @pytest.mark.asyncio
    async def test_websocket_endpoint_setup_failure(self):
        """Test websocket manager connect failure"""
        mock_ws = AsyncMock()
        ocr.manager.connect = AsyncMock(side_effect=Exception("Connection Failed"))

        await ocr.websocket_endpoint(mock_ws, "task_ws_fail")

        # Verify manager.disconnect was NOT called because connect failed?
        # Check logic: line 389 logs error
        # Effectively we just want to ensure it doesn't crash
        pass

    @pytest.mark.asyncio
    async def test_websocket_endpoint_loop_exception(self):
        """Test exception inside websocket loop"""
        mock_ws = AsyncMock()
        mock_ws.receive_text.side_effect = Exception("Loop Error")

        ocr.manager.connect = AsyncMock()
        ocr.manager.disconnect = MagicMock()

        await ocr.websocket_endpoint(mock_ws, "task_loop_fail")

        ocr.manager.disconnect.assert_called()

    @pytest.mark.asyncio
    async def test_export_text_status_check(self):
        """Test export text checks status"""
        task_id = "processing_task"
        ocr.results[task_id] = {"status": "processing"}

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            await ocr.export_text(task_id)
        assert exc.value.status_code == 400
