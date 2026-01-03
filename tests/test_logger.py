# -*- coding: utf-8 -*-
from paddleocr_toolkit.utils.logger import setup_logger
from unittest.mock import MagicMock, patch
from pathlib import Path


class TestLoggerUltra:
    def test_setup_logger_file_logging(self):
        with patch("pathlib.Path.mkdir"), patch("logging.FileHandler") as mock_handler:
            setup_logger(name="file_logger", log_file=Path("test.log"))
            mock_handler.assert_called()
