# -*- coding: utf-8 -*-
"""
Rich UI 測試
測試 paddleocr_toolkit/cli/rich_ui.py
"""

from unittest.mock import MagicMock, patch

import pytest


class TestRichUI:
    """測試 Rich UI 模組"""

    def test_import_rich_ui(self):
        """測試匯入 Rich UI 模組"""
        try:
            from paddleocr_toolkit.cli.rich_ui import RichUI

            assert RichUI is not None
        except ImportError:
            pytest.skip("RichUI not available")

    def test_rich_ui_init(self):
        """測試 Rich UI 初始化"""
        try:
            from paddleocr_toolkit.cli.rich_ui import RichUI

            ui = RichUI()
            assert ui is not None
        except ImportError:
            pytest.skip("RichUI not available")

    def test_rich_ui_has_console(self):
        """測試 Rich UI 有 console 屬性"""
        try:
            from paddleocr_toolkit.cli.rich_ui import RichUI

            ui = RichUI()
            assert hasattr(ui, "console") or hasattr(ui, "_console")
        except ImportError:
            pytest.skip("RichUI not available")


class TestProgressBar:
    """測試進度條"""

    def test_import_progress(self):
        """測試匯入進度條相關類別"""
        try:
            from paddleocr_toolkit.cli.rich_ui import create_progress_bar

            assert callable(create_progress_bar)
        except ImportError:
            # 嘗試其他可能的匯入
            try:
                from paddleocr_toolkit.cli.rich_ui import RichUI

                ui = RichUI()
                assert hasattr(ui, "create_progress") or hasattr(ui, "show_progress")
            except ImportError:
                pytest.skip("Progress bar not available")


class TestTableOutput:
    """測試表格輸出"""

    def test_import_table(self):
        """測試匯入表格類別"""
        try:
            from paddleocr_toolkit.cli.rich_ui import RichUI

            ui = RichUI()
            assert hasattr(ui, "create_table") or hasattr(ui, "print_table")
        except ImportError:
            pytest.skip("Table output not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
