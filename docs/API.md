# API 參考文件 (API Reference)

## 🐍 Python SDK (Facade)

`PaddleOCRFacade` 提供了最簡單的方式將 OCR 功能整合到您的 Python 應用程式中。

### 引入
```python
from paddle_ocr_facade import PaddleOCRFacade
```

### 初始化 `PaddleOCRFacade`

```python
def __init__(self, mode: str = "basic", config_path: str = None, **kwargs)
```

**參數**:
- `mode` (str): 運作模式，可選 `"basic"`, `"hybrid"`, `"structure"`。
- `config_path` (str, optional): 自定義 YAML 設定檔路徑。
- `**kwargs`: 覆蓋設定檔的額外參數 (如 `use_gpu=True`)。

### 方法 `process`

```python
def process(self, input_path: str, output_dir: str = None, **kwargs) -> Dict[str, Any]
```

**參數**:
- `input_path` (str): PDF 或圖片檔案路徑。
- `output_dir` (str, optional): 輸出目錄。如果不指定，則根據設定決定是否生成檔案。
- `**kwargs`: 執行時覆蓋參數 (如 `dpi=300`)。

**返回 (Dict)**:
- `text_content` (List[str]): 提取的文字內容列表。
- `pages_processed` (int): 處理頁數。
- `output_files` (Dict[str, str]): 生成的檔案路徑 (PDF, Markdown, JSON 等)。
- `ocr_results` (List[OCRResult]): 詳細的 OCR 對象列表 (包含座標、信心度)。

### 範例

```python
facade = PaddleOCRFacade(mode="hybrid")
result = facade.process("contract.pdf", dpi=300)

print(result["text_content"][0])  # 第一頁文字
```

---

## 🌐 REST API

啟動 API 伺服器後 (預設 `http://localhost:8000`)，可用於遠端呼叫。完整 Swagger 文件請訪問 `/docs`。

### 1. 提交 OCR 任務

**POST** `/api/ocr/predict`

上傳檔案並開始 OCR 處理。

**Request (Multipart/Form-Data)**:
- `file`: (File) 目標檔案 (PDF/Image)。
- `mode`: (String) 處理模式 (`basic`, `hybrid`)。
- `enable_searchable_pdf`: (Boolean) 是否生成 PDF。

**Response (JSON)**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Task submitted successfully"
}
```

### 2. 查詢任務狀態

**GET** `/api/ocr/status/{task_id}`

**Response (JSON)**:
```json
{
  "task_id": "550e8400-...",
  "status": "completed",
  "progress": 100,
  "result": {
    "pages": 5,
    "download_url": "/api/files/download/result.zip"
  }
}
```

### 3. 系統健康檢查

**GET** `/health`

**Response (JSON)**:
```json
{
  "status": "healthy",
  "version": "3.3.0",
  "components": {
    "ocr_engine": "ready",
    "db": "connected"
  }
}
```

### 4. 系統指標 (Metrics)

**GET** `/api/metrics`

返回 CPU、記憶體使用量與當前佇列狀態。
