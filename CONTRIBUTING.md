# Contributing to PaddleOCR Toolkit

感謝你考慮為 PaddleOCR Toolkit 做貢獻！

---

## 📋 目錄

- [行為準則](#行為準則)
- [如何貢獻](#如何貢獻)
- [開發設定](#開發設定)
- [提交指南](#提交指南)
- [程式碼規範](#程式碼規範)
- [測試要求](#測試要求)

---

## 行為準則

本專案採用 [Contributor Covenant](CODE_OF_CONDUCT.md) 行為準則。參與本專案即表示你同意遵守其條款。

---

## 如何貢獻

### 回報 Bug

在提交 Bug 回報前，請先搜尋現有的 Issues，確保問題尚未被回報。

**Bug 回報應包含**:

- 清晰的標題
- 詳細的描述
- 重現步驟
- 預期行為
- 實際行為
- 環境資訊（Python 版本、作業系統等）
- 錯誤日誌誌

### 建議功能

我們歡迎新功能建議！請在 Issue 中：

- 描述功能的用途
- 解釋為什麼需要這個功能
- 提供使用範例

### 提交 Pull Request

1. Fork 儲存庫
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

---

## 開發設定

### 環境要求

- Python 3.8+
- 虛擬環境工具 (venv, conda)

### 安裝開發環境

```bash
# 克隆儲存庫
git clone https://github.com/danwin47-sys/paddleocr-toolkit.git
cd paddleocr-toolkit

# 建立虛擬環境
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 安裝開發依賴
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 執行測試

```bash
# 執行所有測試
pytest

# 執行帶覆蓋率的測試
pytest --cov=paddleocr_toolkit tests/

# 執行特定測試
pytest tests/test_core_models.py
```

---

## 提交指南

### Commit 訊息格式

我們使用 [Conventional Commits](https://www.conventionalcommits.org/) 規範：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**類型**:

- `feat`: 新功能
- `fix`: Bug 修正
- `docs`: 文件更新
- `style`: 程式碼格式（不影響功能）
- `refactor`: 重構
- `test`: 測試相關
- `chore`: 建置/工具變更

**範例**:

```
feat(ocr): add support for formula recognition

Implement PP-FormulaNet integration for mathematical
formula recognition in documents.

Closes #123
```

---

## 程式碼規範

### Python 程式碼風格

遵循 [PEP 8](https://pep8.org/) 規範，使用以下工具：

```bash
# 程式碼格式化
black paddleocr_toolkit/ tests/

# 匯入排序
isort paddleocr_toolkit/ tests/

# 程式碼檢查
flake8 paddleocr_toolkit/

# 型別檢查
mypy paddleocr_toolkit/
```

### 文件字串 (Docstrings)

使用 Google 風格的 docstrings：

```python
def process_image(image_path: str, dpi: int = 150) -> List[OCRResult]:
    """處理單張圖片
    
    Args:
        image_path: 圖片檔案路徑
        dpi: 解析度，預設 150
        
    Returns:
        OCR 結果列表
        
    Raises:
        FileNotFoundError: 圖片檔案不存在時
        
    Example:
        >>> results = process_image("doc.jpg", dpi=200)
        >>> print(len(results))
        10
    """
    pass
```

### 型別提示 (Type Hints)

所有公開函式都應該有型別提示：

```python
from typing import List, Optional, Dict

def get_config(path: Optional[str] = None) -> Dict[str, Any]:
    """載入設定檔"""
    pass
```

---

## 測試要求

### 單元測試

所有新功能都必須包含測試：

```python
def test_new_feature():
    """測試新功能"""
    tool = PaddleOCRTool(mode="basic")
    result = tool.new_feature()
    
    assert result is not None
    assert len(result) > 0
```

### 測試覆蓋率

- 目標覆蓋率：85%+
- 新增程式碼覆蓋率：90%+

```bash
pytest tests/ --cov=paddleocr_toolkit --cov-report=term-missing
```

### 整合測試

對於重要功能，提供端對端測試：

```python
def test_complete_workflow():
    """測試完整工作流程"""
    tool = PaddleOCRTool()
    results, _ = tool.process_pdf("test.pdf")
    text = tool.get_text(results)
    assert len(text) > 0
```

---

## Pull Request 檢查清單

提交 PR 前，請確認：

- [ ] 程式碼通過所有測試
- [ ] 新功能有相應測試
- [ ] 測試覆蓋率不降低
- [ ] 程式碼已格式化 (black, isort)
- [ ] 通過程式碼檢查 (flake8, mypy)
- [ ] 更新了相關文件
- [ ] 新增了 docstrings
- [ ] Commit 訊息符合規範
- [ ] 沒有合併衝突

---

## 程式碼審查流程

1. 自動化檢查（CI/CD）
2. 程式碼審查（至少 1 人）
3. 測試驗證
4. 文件更新確認
5. 合併到主分支

---

## 發布流程

1. 更新版本號
2. 更新 CHANGELOG
3. 建立發布標籤
4. 觸發自動發布

---

## 問題與幫助

- 📧 提交 Issue
- 💬 GitHub Discussions
- 📖 查看文件

---

**感謝你的貢獻！** 🎉
