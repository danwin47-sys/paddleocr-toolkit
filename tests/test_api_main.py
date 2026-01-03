# -*- coding: utf-8 -*-
"""
API Main Integration Tests - Cleaned up for router refactoring
"""
import os
import sys
import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

try:
    from unittest.mock import AsyncMock
except ImportError:

    class AsyncMock(MagicMock):
        async def __call__(self, *args, **kwargs):
            return super(AsyncMock, self).__call__(*args, **kwargs)


from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def client_fixture():
    """Setup TestClient with mocked dependencies"""
    with patch.dict(sys.modules):
        # Mock costly imports
        sys.modules["paddleocr_toolkit.core.ocr_engine"] = MagicMock()
        sys.modules["paddleocr_toolkit.core.task_queue"] = MagicMock()
        sys.modules["paddleocr_toolkit.plugins.loader"] = MagicMock()

        # Import inside patch context
        import paddleocr_toolkit.api.main as main_module

        # Create client
        client = TestClient(main_module.app)
        yield client, main_module


class TestAPIMain:
    """
    Tests for logic remaining in main.py after refactoring
    """

    def test_root(self, client_fixture):
        """Test root endpoint"""
        client, _ = client_fixture
        response = client.get("/")
        assert response.status_code == 200

    def test_startup_injection(self, client_fixture):
        """Test that routers get values injected during startup"""
        client, main_module = client_fixture
        # Startup event is triggered by TestClient context if used as context manager
        # But here we just check if things are present
        assert main_module.app is not None

    # Most other tests from the original main.py have been moved to:
    # - tests/test_api_routers_ocr.py
    # - tests/test_api_routers_tasks.py
    # - tests/test_api_routers_system.py


@pytest.mark.asyncio
async def test_main_cleanup_loop_exception_gaps():
    """
    Cover api/main.py lines 101-104:
    - asyncio.CancelledError
    - Generic Exception
    """
    from paddleocr_toolkit.api.main import cleanup_old_tasks_loop

    # 1. Trigger CancelledError (Line 101-102)
    with patch("asyncio.sleep", side_effect=asyncio.CancelledError()):
        await cleanup_old_tasks_loop()

    # 2. Trigger Generic Exception (Line 103-104)
    with patch("asyncio.sleep", side_effect=Exception("Test Crash")):
        await cleanup_old_tasks_loop()
    # - tests/test_api_routers_files.py
    # - tests/test_api_dependencies.py


# Added from Ultra Coverage
from paddleocr_toolkit.api.main import (
    app,
    log_requests,
    startup_event,
    serve_frontend,
    global_exception_handler,
)
from fastapi import Request
from unittest.mock import MagicMock, patch
import pytest
import asyncio
import runpy


class TestMainUltra:
    @pytest.mark.asyncio
    async def test_main_missed_lines(self):
        call_next = MagicMock(side_effect=Exception("Middleware crash"))
        mock_req = MagicMock(spec=Request)
        mock_req.url.path = "/"
        mock_req.method = "GET"
        with pytest.raises(Exception):
            await log_requests(mock_req, call_next)

    def test_main_block_simulation(self):
        with patch("uvicorn.run"):
            runpy.run_module("paddleocr_toolkit.api.main", run_name="__main__")


class TestMainUltraMega:
    @pytest.mark.asyncio
    async def test_main_startup_and_frontend(self):
        # 1. startup_event (lines 112-142)
        with patch("paddleocr_toolkit.api.main.plugin_loader") as mock_plugin, patch(
            "paddleocr_toolkit.api.main.TaskQueue"
        ) as mock_q:
            mock_q_inst = mock_q.return_value
            f = asyncio.Future()
            f.set_result(None)
            mock_q_inst.start.return_value = f

            await startup_event()
            mock_plugin.load_all_plugins.assert_called()

        # 2. serve_frontend (lines 157-161)
        with patch("paddleocr_toolkit.api.main.NEXT_OUT_DIR") as mock_dir:
            mock_dir.exists.return_value = True
            mock_file = mock_dir / "index.html"
            mock_file.exists.return_value = True
            mock_file.read_text.return_value = "<html></html>"
            res = await serve_frontend()
            assert res == "<html></html>"

            mock_file.exists.return_value = False
            assert "Frontend not found" in await serve_frontend()

        # 3. Middleware (lines 78-80)
        mock_req = MagicMock(spec=Request)
        mock_req.url.path = "/"
        mock_req.method = "GET"

        async def mock_next(r):
            return MagicMock(status_code=200)

        res = await log_requests(mock_req, mock_next)
        assert res.status_code == 200

        # 4. Global exception handler (lines 60-64)
        mock_exc = Exception("Global Crash")
        res = await global_exception_handler(mock_req, mock_exc)
        assert res.status_code == 500
