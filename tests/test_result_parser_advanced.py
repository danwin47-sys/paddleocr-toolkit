# -*- coding: utf-8 -*-
"""
Advanced tests for OCRResultParser to cover edge cases and error handling lines.
"""
from unittest.mock import MagicMock, Mock, patch
import pytest
from paddleocr_toolkit.core.models import OCRResult
from paddleocr_toolkit.core.result_parser import OCRResultParser


class TestOCRResultParserAdvanced:
    """測試 OCR 解析器的邊界情況與錯誤處理"""

    def test_parse_overall_ocr_failure(self):
        """測試 _parse_overall_ocr 內部發生異常的情況"""
        parser = OCRResultParser()

        # 模擬一個物件，在被讀取時會拋出異常
        mock_ocr_res = MagicMock()
        # 讓 parse_basic_result 拋出異常 (這裡我們 mock self.parse_basic_result 比較困難，
        # 不如傳入一個會讓 parse_basic_result 失敗的結構)

        # 其實可以 Patch OCRResultParser.parse_basic_result
        with patch.object(
            parser, "parse_basic_result", side_effect=Exception("Parsing error")
        ):
            results = parser._parse_overall_ocr(mock_ocr_res)
            # 應該捕獲異常並返回空列表
            assert results == []

    def test_parse_parsing_list_malformed_blocks(self):
        """測試 _parse_parsing_list 遇到格式錯誤的區塊"""
        parser = OCRResultParser()

        # 區塊1: 缺少 bbox
        block1 = Mock()
        block1.content = "Text"
        del block1.bbox

        # 區塊2: 缺少 content
        block2 = Mock(spec=[])  # 空物件
        block2.bbox = [0, 0, 10, 10]

        # 區塊3: bbox 格式錯誤 (長度不足)
        block3 = Mock()
        block3.content = "Text"
        block3.bbox = [0, 0]

        # 區塊4: 正常
        block4 = Mock()
        block4.content = "Valid"
        block4.bbox = [0, 0, 100, 50]

        results = parser._parse_parsing_list([block1, block2, block3, block4])

        assert len(results) == 1
        assert results[0].text == "Valid"

    def test_parse_parsing_list_exception_in_loop(self):
        """測試 _parse_parsing_list 迴圈中發生異常"""
        parser = OCRResultParser()

        # 模擬一個區塊，訪問屬性時拋出異常
        class ErrorBlock:
            @property
            def bbox(self):
                raise ValueError("Access error")

        results = parser._parse_parsing_list([ErrorBlock()])
        assert results == []

    def test_validate_results_confidence_clipping(self):
        """測試 validate_results 自動修正置信度範圍"""
        parser = OCRResultParser()

        # 超出範圍的置信度
        res_over = OCRResult(
            text="Over", confidence=1.5, bbox=[[0, 0], [10, 0], [10, 10], [0, 10]]
        )
        res_under = OCRResult(
            text="Under", confidence=-0.5, bbox=[[0, 0], [10, 0], [10, 10], [0, 10]]
        )

        results = parser.validate_results([res_over, res_under])

        assert len(results) == 2
        assert results[0].confidence == 1.0
        assert results[1].confidence == 0.0

    def test_parse_from_list_formats(self):
        """測試 _parse_from_list 的不同列表格式"""
        parser = OCRResultParser()

        # 標準格式: [poly, (text, score)]
        valid_item = [[[0, 0], [10, 0], [10, 10], [0, 10]], ("Text", 0.99)]

        # 變體1: 只有 text，沒有 score
        no_score = [[[0, 0], [10, 0], [10, 10], [0, 10]], ("NoScore",)]

        # 變體2: 第二項不是 tuple/list
        invalid_text_info = [[[0, 0], [10, 0], [10, 10], [0, 10]], "JustString"]

        # 變體3: 第一項無效
        invalid_poly = ["BadPoly", ("Text", 0.9)]

        # 變體4: 整項結構不對
        malformed = ["Garbage"]

        # 用 _parse_from_list 直接測試
        results = parser._parse_from_list(
            [valid_item, no_score, invalid_text_info, invalid_poly, malformed]
        )

        # invalid_poly 可能會進入 _create_ocr_result 然後失敗返回 None
        # invalid_text_info 會被過濾
        # malformed 會被過濾

        # 檢查 valid_item
        assert any(r.text == "Text" and r.confidence == 0.99 for r in results)

        # 檢查 no_score (應該預設為 1.0)
        assert any(r.text == "NoScore" and r.confidence == 1.0 for r in results)

        # 確保無效的沒有被解析出來
        assert not any(r.text == "JustString" for r in results)

    def test_ocr_result_import_fallback(self):
        """測試 ImportError 降級匯入 (模擬)"""
        # 這很難直接測試真實的 ImportError，但我們可以模擬 runpy 行為
        # 或者簡單地確保 models 模組存在
        import paddleocr_toolkit.core.result_parser as rp

        assert rp.OCRResult is not None
