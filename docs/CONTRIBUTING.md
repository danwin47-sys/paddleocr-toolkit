# 貢獻指南 (Contributing Guide)

感謝您有興趣貢獻 PaddleOCR Toolkit！我們歡迎任何形式的貢獻，包括錯誤回報、功能建議、文件改進與程式碼提交。

## 🛠️ 開發環境設置

1.  **Fork 本專案** 並 Clone 到本地。
2.  **建立開發環境**：
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  **安裝開發依賴**：
    ```bash
    pip install pytest pytest-cov black isort
    ```

## 🧪 測試規範

本專案極度重視代碼品質與測試覆蓋率。所有新功能或修復必須包含相應的測試。

- **測試框架**: 使用 `pytest`。
- **覆蓋率要求**: 新模組覆蓋率至少需達 **90%**。
- **執行測試**:
    ```bash
    # 執行所有測試
    pytest

    # 執行特定模組測試
    pytest tests/test_hybrid_processor.py

    # 檢查覆蓋率
    pytest --cov=paddleocr_toolkit
    ```

## 🎨 代碼風格

我們遵循 Python 社群標準：

- **格式化**: 使用 `black` 進行代碼格式化。
- **導入排序**: 使用 `isort`。
- **類型提示**: 所有函數與方法應包含 Type Hints。

```bash
# 提交前請執行格式化
black .
isort .
```

## 📝 提交 Pull Request (PR)

1.  確保所有測試通過 (`pytest`)。
2.  確保代碼已格式化。
3.  PR 標題應簡潔描述變更 (例如: `feat: add support for Claude 3`).
4.  在 PR 描述中詳細說明變更內容與測試方法。

## 🐛 回報問題

請使用 GitHub Issues 回報錯誤。回報時請提供：
- 使用的 PaddleOCR Toolkit 版本
- 錯誤日誌 (Log)
- 重現步驟或範例檔案

---
再次感謝您的貢獻！一同打造更強大的文件處理工具。
