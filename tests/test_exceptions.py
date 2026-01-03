# -*- coding: utf-8 -*-
"""
測試 paddleocr_toolkit.exceptions 模組

此測試文件涵蓋所有自訂例外類別，確保 100% 覆蓋率。
"""
import pytest
from paddleocr_toolkit.exceptions import (
    OCRToolkitError,
    FileProcessingError,
    OCRProcessingError,
    ModelLoadError,
    ConfigurationError,
    APIError,
)


class TestOCRToolkitError:
    """測試基礎例外類別"""

    def test_raise_base_error(self):
        """測試拋出基礎例外"""
        with pytest.raises(OCRToolkitError) as exc_info:
            raise OCRToolkitError("測試錯誤訊息")
        assert "測試錯誤訊息" in str(exc_info.value)

    def test_base_error_is_exception(self):
        """測試基礎例外繼承自 Exception"""
        assert issubclass(OCRToolkitError, Exception)

    def test_base_error_with_no_message(self):
        """測試無訊息的例外"""
        with pytest.raises(OCRToolkitError):
            raise OCRToolkitError()


class TestFileProcessingError:
    """測試文件處理錯誤"""

    def test_raise_file_error(self):
        """測試拋出文件處理錯誤"""
        with pytest.raises(FileProcessingError) as exc_info:
            raise FileProcessingError("無法讀取文件: test.pdf")
        assert "test.pdf" in str(exc_info.value)

    def test_file_error_inheritance(self):
        """測試繼承關係"""
        assert issubclass(FileProcessingError, OCRToolkitError)
        assert issubclass(FileProcessingError, Exception)

    def test_file_error_with_path(self):
        """測試帶路徑的錯誤"""
        file_path = "/path/to/missing/file.txt"
        with pytest.raises(FileProcessingError) as exc_info:
            raise FileProcessingError(f"File not found: {file_path}")
        assert file_path in str(exc_info.value)


class TestOCRProcessingError:
    """測試 OCR 處理錯誤"""

    def test_raise_ocr_error(self):
        """測試拋出 OCR 處理錯誤"""
        with pytest.raises(OCRProcessingError) as exc_info:
            raise OCRProcessingError("OCR 引擎處理失敗")
        assert "處理失敗" in str(exc_info.value)

    def test_ocr_error_inheritance(self):
        """測試繼承關係"""
        assert issubclass(OCRProcessingError, OCRToolkitError)

    def test_ocr_error_with_details(self):
        """測試帶詳細資訊的錯誤"""
        with pytest.raises(OCRProcessingError) as exc_info:
            raise OCRProcessingError("Page 5 processing failed: timeout")
        assert "Page 5" in str(exc_info.value)
        assert "timeout" in str(exc_info.value)


class TestModelLoadError:
    """測試模型加載錯誤"""

    def test_raise_model_error(self):
        """測試拋出模型加載錯誤"""
        with pytest.raises(ModelLoadError) as exc_info:
            raise ModelLoadError("無法加載 PaddleOCR 模型")
        assert "PaddleOCR" in str(exc_info.value)

    def test_model_error_inheritance(self):
        """測試繼承關係"""
        assert issubclass(ModelLoadError, OCRToolkitError)

    def test_model_error_with_model_name(self):
        """測試帶模型名稱的錯誤"""
        with pytest.raises(ModelLoadError) as exc_info:
            raise ModelLoadError("Failed to load model: ch_PP-OCRv3_det")
        assert "ch_PP-OCRv3_det" in str(exc_info.value)


class TestConfigurationError:
    """測試配置錯誤"""

    def test_raise_config_error(self):
        """測試拋出配置錯誤"""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("配置文件格式錯誤")
        assert "配置文件" in str(exc_info.value)

    def test_config_error_inheritance(self):
        """測試繼承關係"""
        assert issubclass(ConfigurationError, OCRToolkitError)

    def test_config_error_with_key(self):
        """測試帶配置鍵的錯誤"""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Missing required config key: API_KEY")
        assert "API_KEY" in str(exc_info.value)


class TestAPIError:
    """測試 API 調用錯誤"""

    def test_raise_api_error(self):
        """測試拋出 API 錯誤"""
        with pytest.raises(APIError) as exc_info:
            raise APIError("Gemini API 調用失敗")
        assert "Gemini" in str(exc_info.value)

    def test_api_error_inheritance(self):
        """測試繼承關係"""
        assert issubclass(APIError, OCRToolkitError)

    def test_api_error_with_status_code(self):
        """測試帶狀態碼的錯誤"""
        with pytest.raises(APIError) as exc_info:
            raise APIError("API request failed with status 429: Rate limit exceeded")
        assert "429" in str(exc_info.value)
        assert "Rate limit" in str(exc_info.value)


class TestExceptionHierarchy:
    """測試例外層級結構"""

    def test_all_exceptions_inherit_from_base(self):
        """測試所有例外都繼承自基礎類別"""
        exceptions = [
            FileProcessingError,
            OCRProcessingError,
            ModelLoadError,
            ConfigurationError,
            APIError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, OCRToolkitError)
            assert issubclass(exc_class, Exception)

    def test_catch_with_base_exception(self):
        """測試使用基礎例外捕獲所有子例外"""
        exceptions_to_test = [
            FileProcessingError("test"),
            OCRProcessingError("test"),
            ModelLoadError("test"),
            ConfigurationError("test"),
            APIError("test"),
        ]

        for exc in exceptions_to_test:
            with pytest.raises(OCRToolkitError):
                raise exc

    def test_exception_instances(self):
        """測試例外實例化"""
        file_err = FileProcessingError("file error")
        ocr_err = OCRProcessingError("ocr error")
        model_err = ModelLoadError("model error")
        config_err = ConfigurationError("config error")
        api_err = APIError("api error")

        assert isinstance(file_err, OCRToolkitError)
        assert isinstance(ocr_err, OCRToolkitError)
        assert isinstance(model_err, OCRToolkitError)
        assert isinstance(config_err, OCRToolkitError)
        assert isinstance(api_err, OCRToolkitError)


class TestExceptionModule:
    """測試模組級別功能"""

    def test_all_exports(self):
        """測試 __all__ 導出"""
        from paddleocr_toolkit import exceptions

        expected_exports = [
            "OCRToolkitError",
            "FileProcessingError",
            "OCRProcessingError",
            "ModelLoadError",
            "ConfigurationError",
            "APIError",
        ]

        for name in expected_exports:
            assert hasattr(exceptions, name)
            assert name in exceptions.__all__

    def test_module_docstring(self):
        """測試模組文檔字串"""
        from paddleocr_toolkit import exceptions

        assert exceptions.__doc__ is not None
        assert "自定義異常" in exceptions.__doc__
