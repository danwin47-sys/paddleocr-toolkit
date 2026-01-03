# -*- coding: utf-8 -*-
"""
測試 paddleocr_toolkit.core.logging_utils 模組
"""
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import pytest
from paddleocr_toolkit.core.logging_utils import setup_logging


class TestSetupLogging:
    """測試日誌設定功能"""

    def teardown_method(self):
        """每個測試後清理 logging handlers"""
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

    def test_setup_logging_with_custom_file(self, tmp_path):
        """測試指定日誌檔案路徑"""
        log_file = tmp_path / "custom.log"
        result = setup_logging(str(log_file))

        assert result == str(log_file)
        assert log_file.exists()
        assert len(logging.root.handlers) == 2  # file + console

    def test_setup_logging_auto_generate_file(self, tmp_path):
        """測試自動生成日誌檔案"""
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            result = setup_logging(None)

            assert "logs" in result
            assert "paddle_ocr_" in result
            assert ".log" in result
            assert Path(result).exists()

    def test_setup_logging_creates_logs_directory(self, tmp_path):
        """測試自動建立 logs 目錄"""
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            setup_logging(None)
            logs_dir = tmp_path / "logs"
            assert logs_dir.exists()
            assert logs_dir.is_dir()

    def test_setup_logging_removes_existing_handlers(self, tmp_path):
        """測試移除現有 handlers"""
        # 先添加一些 handlers
        dummy_handler = logging.StreamHandler()
        logging.root.addHandler(dummy_handler)
        logging.root.addHandler(logging.StreamHandler())

        assert len(logging.root.handlers) >= 2

        log_file = tmp_path / "test.log"
        setup_logging(str(log_file))

        # 應該只有兩個新的 handlers (file + console)
        assert len(logging.root.handlers) == 2
        assert dummy_handler not in logging.root.handlers

    def test_setup_logging_file_handler_config(self, tmp_path):
        """測試 file handler 配置"""
        log_file = tmp_path / "test.log"
        setup_logging(str(log_file))

        file_handler = None
        for handler in logging.root.handlers:
            if isinstance(handler, logging.FileHandler):
                file_handler = handler
                break

        assert file_handler is not None
        assert file_handler.level == logging.INFO
        assert file_handler.formatter is not None

    def test_setup_logging_console_handler_config(self, tmp_path):
        """測試 console handler 配置"""
        log_file = tmp_path / "test.log"
        setup_logging(str(log_file))

        console_handler = None
        for handler in logging.root.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(
                handler, logging.FileHandler
            ):
                console_handler = handler
                break

        assert console_handler is not None
        assert console_handler.level == logging.INFO
        assert console_handler.stream == sys.stdout

    def test_setup_logging_formatter(self, tmp_path):
        """測試 formatter 格式"""
        log_file = tmp_path / "test.log"
        setup_logging(str(log_file))

        for handler in logging.root.handlers:
            formatter = handler.formatter
            assert formatter is not None
            # 檢查格式字串包含必要元素
            assert "%(asctime)s" in formatter._fmt
            assert "%(levelname)s" in formatter._fmt
            assert "%(message)s" in formatter._fmt

    def test_setup_logging_root_level(self, tmp_path):
        """測試 root logger 級別設定"""
        log_file = tmp_path / "test.log"
        setup_logging(str(log_file))

        assert logging.root.level == logging.INFO

    def test_setup_logging_writes_initial_log(self, tmp_path):
        """測試寫入初始日誌記錄"""
        log_file = tmp_path / "test.log"
        setup_logging(str(log_file))

        # 讀取日誌檔案內容
        content = log_file.read_text(encoding="utf-8")

        assert "=" * 60 in content
        assert "日誌檔案" in content
        assert str(log_file) in content

    def test_setup_logging_flushes_handlers(self, tmp_path):
        """測試 handlers flush 操作"""
        log_file = tmp_path / "test.log"

        with patch.object(logging.FileHandler, "flush") as mock_flush:
            setup_logging(str(log_file))
            # flush 應該被調用（至少一次）
            assert mock_flush.call_count >= 1

    def test_setup_logging_multiple_calls(self, tmp_path):
        """測試多次調用 setup_logging"""
        log_file1 = tmp_path / "test1.log"
        log_file2 = tmp_path / "test2.log"

        setup_logging(str(log_file1))
        handlers_count1 = len(logging.root.handlers)

        setup_logging(str(log_file2))
        handlers_count2 = len(logging.root.handlers)

        # 應該還是只有兩個 handlers（舊的被移除）
        assert handlers_count1 == handlers_count2 == 2

    def test_setup_logging_utf8_encoding(self, tmp_path):
        """測試 UTF-8 編碼支援"""
        log_file = tmp_path / "test.log"
        setup_logging(str(log_file))

        # 寫入包含中文的日誌
        logging.info("測試中文日誌：你好世界")

        # 讀取並驗證
        content = log_file.read_text(encoding="utf-8")
        assert "測試中文日誌" in content
        assert "你好世界" in content

    def test_setup_logging_file_mode_write(self, tmp_path):
        """測試檔案以寫入模式開啟（覆蓋舊內容）"""
        log_file = tmp_path / "test.log"

        # 先寫入一些內容
        log_file.write_text("old content")

        # 設定 logging
        setup_logging(str(log_file))

        # 舊內容應該被覆蓋
        content = log_file.read_text(encoding="utf-8")
        assert "old content" not in content
        assert "日誌檔案" in content


class TestLoggingIntegration:
    """測試日誌整合功能"""

    def teardown_method(self):
        """每個測試後清理 logging handlers"""
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

    def test_log_levels(self, tmp_path):
        """測試不同日誌級別"""
        log_file = tmp_path / "levels.log"
        setup_logging(str(log_file))

        logging.debug("Debug message")  # 不應該被記錄
        logging.info("Info message")
        logging.warning("Warning message")
        logging.error("Error message")

        content = log_file.read_text(encoding="utf-8")
        assert "Debug message" not in content
        assert "Info message" in content
        assert "Warning message" in content
        assert "Error message" in content

    def test_console_output(self, tmp_path, capsys):
        """測試控制台輸出"""
        log_file = tmp_path / "console.log"
        setup_logging(str(log_file))

        test_message = "Test console output"
        logging.info(test_message)

        captured = capsys.readouterr()
        assert test_message in captured.out
