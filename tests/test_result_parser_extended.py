# -*- coding: utf-8 -*-
"""
Result Parser 擴展測試 - v1.1.0
補充測試以達到 90% 覆蓋率
"""

import pytest
from unittest.mock import Mock, patch
import logging

from paddleocr_toolkit.core.models import OCRResult
from paddleocr_toolkit.core.result_parser import OCRResultParser


class TestResultParserStrictMode:
    """測試嚴格模式"""
    
    def test_strict_mode_parse_basic_error(self):
        """測試嚴格模式下的基本解析錯誤"""
        parser = OCRResultParser(strict_mode=True)
        
        # 傳入無法迭代的對象
        with pytest.raises(ValueError, match="解析基本 OCR 結果失敗"):
            parser.parse_basic_result(None)
    
    def test_strict_mode_parse_structure_error(self):
        """測試嚴格模式下的結構化解析錯誤"""
        parser = OCRResultParser(strict_mode=True)
        
        with pytest.raises(ValueError, match="解析結構化結果失敗"):
            parser.parse_structure_result(None)
    
    def test_strict_mode_parse_formula_error(self):
        """測試嚴格模式下的公式解析錯誤"""
        parser = OCRResultParser(strict_mode=True)
        
        with pytest.raises(ValueError, match="解析公式結果失敗"):
            parser.parse_formula_result(None)


class TestResultParserErrorHandling:
    """測試錯誤處理"""
    
    def test_create_ocr_result_with_invalid_poly(self):
        """測試處理無效polygon"""
        parser = OCRResultParser()
        
        # _create_ocr_result 是私有方法，通過parse_basic_result測試
        mock_result = Mock()
        mock_result.rec_texts = ["Test"]
        mock_result.rec_scores = [0.9]
        mock_result.dt_polys = [None]  # 無效polygon
        
        results = parser.parse_basic_result([mock_result])
        
        # 應該跳過無效結果
        assert len(results) == 0
    
    def test_parse_structure_overall_ocr_error(self):
        """測試overall_ocr解析錯誤處理"""
        parser = OCRResultParser()
        
        mock_res = Mock()
        mock_res.overall_ocr_res = "invalid"  # 無效格式
        
        # 不應該崩潰，應該優雅處理
        results = parser.parse_structure_result([mock_res])
        assert isinstance(results, list)
    
    def test_parse_parsing_list_with_invalid_block(self):
        """測試parsing_list中的無效block"""
        parser = OCRResultParser()
        
        # 創建有效和無效的blocks混合
        valid_block = Mock()
        valid_block.bbox = [10, 20, 100, 80]
        valid_block.content = "Valid"
        
        invalid_block = Mock()
        invalid_block.bbox = [10, 20]  # bbox太短
        invalid_block.content = "Invalid"
        
        mock_res = Mock()
        mock_res.overall_ocr_res = None
        mock_res.parsing_res_list = [valid_block, invalid_block]
        
        results = parser.parse_structure_result([mock_res])
        
        # 應該只有有效的結果
        assert len(results) == 1
        assert results[0].text == "Valid"
    
    def test_parse_formula_with_dict_format(self):
        """測試解析字典格式的公式"""
        parser = OCRResultParser()
        
        # 字典格式
        dict_formula = {"latex": "x^2 + y^2 = r^2", "confidence": 0.88}
        
        results = parser.parse_formula_result([dict_formula])
        
        assert len(results) == 1
        assert results[0]["latex"] == "x^2 + y^2 = r^2"


class TestValidateResults:
    """測試結果驗證"""
    
    def test_validate_with_confidence_out_of_range(self):
        """測試置信度超出範圍的修正"""
        parser = OCRResultParser()
        
        # 置信度超過1.0
        high_conf = OCRResult("Test", 1.5, [[0, 0], [100, 0], [100, 50], [0, 50]])
        
        # 置信度小於0
        low_conf = OCRResult("Test2", -0.5, [[0, 60], [100, 60], [100, 110], [0, 110]])
        
        results = parser.validate_results([high_conf, low_conf])
        
        # 應該修正置信度並保留結果
        assert len(results) == 2
        assert results[0].confidence == 1.0  # 修正為1.0
        assert results[1].confidence == 0.0  # 修正為0.0
    
    def test_validate_removes_empty_text(self):
        """測試移除空文字結果"""
        parser = OCRResultParser()
        
        empty = OCRResult("", 0.9, [[0, 0], [100, 0], [100, 50], [0, 50]])
        whitespace = OCRResult("   ", 0.9, [[0, 60], [100, 60], [100, 110], [0, 110]])
        valid = OCRResult("Valid", 0.9, [[0, 120], [100, 120], [100, 170], [0, 170]])
        
        results = parser.validate_results([empty, whitespace, valid])
        
        assert len(results) == 1
        assert results[0].text == "Valid"
    
    def test_validate_removes_invalid_bbox(self):
        """測試移除無效bbox的結果"""
        parser = OCRResultParser()
        
        invalid_bbox1 = OCRResult("Test", 0.9, [])  # 空bbox
        invalid_bbox2 = OCRResult("Test2", 0.9, [[0, 0]])  # bbox太短
        valid = OCRResult("Valid", 0.9, [[0, 0], [100, 0], [100, 50], [0, 50]])
        
        results = parser.validate_results([invalid_bbox1, invalid_bbox2, valid])
        
        assert len(results) == 1
        assert results[0].text == "Valid"


class TestSortByPosition:
    """測試位置排序"""
    
    def test_sort_unknown_order_returns_original(self):
        """測試未知排序順序返回原始順序"""
        parser = OCRResultParser()
        
        bottom = OCRResult("Bottom", 0.9, [[0, 100], [100, 100], [100, 150], [0, 150]])
        top = OCRResult("Top", 0.9, [[0, 0], [100, 0], [100, 50], [0, 50]])
        
        # 使用未知的排序順序
        results = parser.sort_by_position([bottom, top], reading_order="unknown")
        
        # 應該保持原始順序
        assert results[0].text == "Bottom"
        assert results[1].text == "Top"


class TestParseEdgeCases:
    """測試邊界情況"""
    
    def test_parse_empty_structure_result(self):
        """測試解析空結構化結果"""
        parser = OCRResultParser()
        
        results = parser.parse_structure_result([])
        assert len(results) == 0
    
    def test_parse_structure_with_empty_parsing_list(self):
        """測試空parsing_list"""
        parser = OCRResultParser()
        
        mock_res = Mock()
        mock_res.overall_ocr_res = None
        mock_res.parsing_res_list = []
        
        results = parser.parse_structure_result([mock_res])
        assert len(results) == 0
    
    def test_parse_structure_with_empty_content(self):
        """測試空內容的block"""
        parser = OCRResultParser()
        
        empty_block = Mock()
        empty_block.bbox = [10, 20, 100, 80]
        empty_block.content = ""  # 空內容
        
        mock_res = Mock()
        mock_res.overall_ocr_res = None
        mock_res.parsing_res_list = [empty_block]
        
        results = parser.parse_structure_result([mock_res])
        
        # 空內容應該被跳過
        assert len(results) == 0
    
    def test_filter_confidence_with_empty_list(self):
        """測試過濾空列表"""
        parser = OCRResultParser()
        
        results = parser.filter_by_confidence([], min_confidence=0.5)
        assert results == []
    
    def test_sort_empty_list(self):
        """測試排序空列表"""
        parser = OCRResultParser()
        
        results = parser.sort_by_position([], reading_order="top-to-bottom")
        assert results == []


class TestParseComplexStructure:
    """測試複雜結構解析"""
    
    def test_parse_structure_prefers_overall_ocr(self):
        """測試優先使用overall_ocr_res"""
        parser = OCRResultParser()
        
        # 同時提供兩種結果
        mock_ocr = Mock()
        mock_ocr.rec_texts = ["From OCR"]
        mock_ocr.rec_scores = [0.95]
        mock_ocr.dt_polys = [[[0, 0], [100, 0], [100, 50], [0, 50]]]
        
        mock_block = Mock()
        mock_block.bbox = [0, 0, 100, 50]
        mock_block.content = "From Parsing"
        
        mock_res = Mock()
        mock_res.overall_ocr_res = mock_ocr
        mock_res.parsing_res_list = [mock_block]
        
        results = parser.parse_structure_result([mock_res])
        
        # 應該優先使用overall_ocr_res
        assert len(results) == 1
        assert results[0].text == "From OCR"
    
    def test_parse_structure_fallback_to_parsing_list(self):
        """測試降級使用parsing_list"""
        parser = OCRResultParser()
        
        mock_block = Mock()
        mock_block.bbox = [0, 0, 100, 50]
        mock_block.content = "From Parsing"
        
        mock_res = Mock()
        mock_res.overall_ocr_res = None  # 沒有overall_ocr
        mock_res.parsing_res_list = [mock_block]
        
        results = parser.parse_structure_result([mock_res])
        
        # 應該使用parsing_list
        assert len(results) == 1
        assert results[0].text == "From Parsing"


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
