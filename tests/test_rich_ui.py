# -*- coding: utf-8 -*-
"""
Rich UI 測試
測試 paddleocr_toolkit/cli/rich_ui.py
"""

import pytest
import sys
import io
import importlib
from unittest.mock import MagicMock, patch

# Import the actual module
import paddleocr_toolkit.cli.rich_ui as rich_ui
from paddleocr_toolkit.cli.rich_ui import (
    print_banner,
    print_success,
    print_error,
    print_warning,
    print_info,
    create_results_table,
    create_progress_bar,
    print_performance_summary,
    print_logo,
)


class TestRichUIFunctional:
    """測試 Rich UI 功能函式"""

    def test_has_rich_flag(self):
        """測試此環境是否安裝了 rich"""
        # 如果環境中有 rich，HAS_RICH 應為 True
        # 如果沒有，則為 False，但至少變數要存在
        assert hasattr(rich_ui, "HAS_RICH")

    def test_print_functions(self):
        """測試各種列印函式是否可呼叫"""
        # 這裡主要測試執行不會崩潰，實際輸出效果難以斷言，除非 mock console
        with patch("paddleocr_toolkit.cli.rich_ui.console") as mock_console:
            # 確保有 console 才能測試 rich 分支
            if rich_ui.HAS_RICH:
                print_banner()
                print_success("msg")
                print_error("msg")
                print_warning("msg")
                print_info("msg")
                print_logo()

                assert mock_console.print.call_count >= 1

    def test_create_results_table(self):
        """測試表格建立"""
        if not rich_ui.HAS_RICH:
            pytest.skip("Rich not installed")

        data = [(1, 100, 0.95), (2, 50, 0.85)]
        table = create_results_table(data)
        assert table is not None
        # rich.table.Table instance
        assert type(table).__name__ == "Table"

    def test_create_progress_bar(self):
        """測試進度條建立"""
        if not rich_ui.HAS_RICH:
            pytest.skip("Rich not installed")

        bar = create_progress_bar(100)
        assert bar is not None
        # rich.progress.Progress instance
        assert type(bar).__name__ == "Progress"

    def test_print_performance_summary(self):
        """測試效能摘要列印"""
        if not rich_ui.HAS_RICH:
            pytest.skip("Rich not installed")

        stats = {
            "total_pages": 1,
            "total_time": 1.0,
            "avg_time_per_page": 1.0,
            "peak_memory_mb": 100,
            "total_texts": 50,
        }
        with patch("paddleocr_toolkit.cli.rich_ui.console") as mock_console:
            print_performance_summary(stats)
            mock_console.print.assert_called()


class TestRichUIFallbacks:
    """測試當 Rich 未安裝時的 fallback 行為"""

    def test_fallback_logic_no_rich(self):
        """模擬 HAS_RICH=False"""
        with patch("paddleocr_toolkit.cli.rich_ui.HAS_RICH", False):
            # 攔截 stdout
            f = io.StringIO()
            with patch("sys.stdout", f):
                print_banner()
                print_success("test")
                print_error("test")
                print_warning("test")
                print_info("test")
                print_logo()

                output = f.getvalue()
                assert "PaddleOCR Toolkit" in output
                # Check using the actual icons loaded in the module
                assert f"{rich_ui.ICONS['success']} test" in output
                assert f"{rich_ui.ICONS['error']} test" in output

                assert create_results_table([]) is None
                assert create_progress_bar(10) is None

                print_performance_summary({"check": "val"})
                assert ": val" in f.getvalue()

    def test_import_process_simulation(self):
        """模擬 import 過程中的 ImportError"""
        # 我們不能真正解除安裝 rich，但可以 mock sys.modules
        with patch.dict(sys.modules, {"rich": None}):
            importlib.reload(rich_ui)
            assert rich_ui.HAS_RICH is False
        # 恢復
        importlib.reload(rich_ui)
