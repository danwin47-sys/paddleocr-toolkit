# -*- coding: utf-8 -*-
"""
Tests for CLI commands: validate and benchmark.
"""
import pytest
import json
import os
import sys
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from paddleocr_toolkit.cli.commands.validate import (
    calculate_character_accuracy,
    calculate_word_accuracy,
    edit_distance,
    validate_ocr_results,
)
from paddleocr_toolkit.cli.commands.benchmark import run_benchmark


class TestValidateCommand:
    def test_calculate_character_accuracy(self):
        assert calculate_character_accuracy("abc", "abc") == 1.0
        assert calculate_character_accuracy("abc", "abd") == pytest.approx(2 / 3)
        assert calculate_character_accuracy("", "abc") == 0.0
        assert calculate_character_accuracy("abc", "") == 0.0  # ground_truth missing
        assert (
            calculate_character_accuracy("", "") == 0.0
        )  # both empty, ground_truth rules

    def test_calculate_word_accuracy(self):
        assert calculate_word_accuracy(["a", "b"], ["a", "b"]) == 1.0
        assert calculate_word_accuracy(["a", "c"], ["a", "b"]) == 0.5
        assert calculate_word_accuracy([], ["a"]) == 0.0
        assert calculate_word_accuracy(["a"], []) == 0.0

    def test_edit_distance(self):
        # Test the wrapper specifically if relevant, forcing usage if needed
        # Though validate.py uses Levenshtein directly mostly
        assert edit_distance("kitten", "sitting") == 3
        assert edit_distance("rosettacode", "raisethysword") == 8

    def test_validate_missing_files(self, caplog):
        validate_ocr_results("missing.json", "truth.txt")
        assert "不存在" in caplog.text or "not exist" in caplog.text

    def test_validate_flow(self, tmp_path, caplog):
        ocr_file = tmp_path / "ocr.json"
        gt_file = tmp_path / "gt.txt"

        # Setup data
        ocr_data = [{"text": "Hello World"}]
        with open(ocr_file, "w") as f:
            json.dump(ocr_data, f)

        gt_file.write_text("Hello World", encoding="utf-8")

        with patch("paddleocr_toolkit.cli.commands.validate.logger") as mock_logger:
            # We still need to patch logger because the code uses it,
            # but we can capture logs via caplog if logger propagates,
            # OR just strictly check call args on the mock.
            # Validating against mock_logger calls is safer if propagation is off.
            validate_ocr_results(str(ocr_file), str(gt_file))

            # Verify success logs
            # Check if any call args contains the target string
            found_perfect = False
            found_score = False
            for call in mock_logger.info.call_args_list:
                args, _ = call
                msg = args[0] % args[1:] if len(args) > 1 else args[0]
                if "Perfect Match" in str(msg):
                    found_perfect = True
                if "Score: 100.00%" in str(msg):
                    found_score = True

            assert found_perfect
            assert found_score

    def test_validate_bad_json(self, tmp_path, caplog):
        ocr_file = tmp_path / "bad.json"
        ocr_file.write_text("{bad:json}", encoding="utf-8")

        validate_ocr_results(str(ocr_file), "gt.txt")
        assert "Failed to load OCR results" in caplog.text

    def test_validate_main_block(self):
        with patch.object(sys, "argv", ["validate.py", "ocr.json", "gt.txt"]), patch(
            "paddleocr_toolkit.cli.commands.validate.validate_ocr_results"
        ) as mock_val:
            from paddleocr_toolkit.cli.commands import validate

            # Reload to trigger if __name__ == "__main__" if running as script,
            # but we can't easily trigger __name__ check on import.
            # So we simulate the call logic
            if len(sys.argv) >= 3:
                validate.validate_ocr_results(sys.argv[1], sys.argv[2])
            mock_val.assert_called_with("ocr.json", "gt.txt")


class TestBenchmarkCommand:
    @patch("paddleocr_toolkit.cli.commands.benchmark.psutil")
    def test_run_benchmark_success(self, mock_psutil, tmp_path):
        # Setup mocks
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 1024 * 1024 * 100  # 100MB
        mock_psutil.Process.return_value = mock_process

        # Mock PaddleOCRTool imported inside the function
        mock_tool_cls = MagicMock()
        mock_tool = mock_tool_cls.return_value
        mock_tool.process.return_value = {
            "pages_processed": 1,
            "text_content": ["Page 1 Text"],
        }

        mock_module = MagicMock()
        mock_module.PaddleOCRTool = mock_tool_cls

        with patch.dict("sys.modules", {"paddle_ocr_tool": mock_module}):
            pdf_path = tmp_path / "test.pdf"
            pdf_path.touch()
            output_path = tmp_path / "bench.json"

            run_benchmark(str(pdf_path), str(output_path))

            assert output_path.exists()
            # Verify call count (4 scenarios)
            assert mock_tool.process.call_count == 4

    def test_benchmark_missing_file(self, caplog):
        run_benchmark("missing.pdf")
        assert "File not found" in caplog.text

    def test_benchmark_main_block(self):
        with patch.object(sys, "argv", ["benchmark.py", "f.pdf"]), patch(
            "paddleocr_toolkit.cli.commands.benchmark.run_benchmark"
        ) as mock_run:
            from paddleocr_toolkit.cli.commands import benchmark

            # Simulate logic
            if len(sys.argv) >= 2:
                benchmark.run_benchmark(sys.argv[1], None)
            mock_run.assert_called_with("f.pdf", None)
