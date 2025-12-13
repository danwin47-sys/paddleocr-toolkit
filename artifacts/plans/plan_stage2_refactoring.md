# 階段 2 重構計畫：過長函數與重複邏輯

> 建立時間：2024-12-13 23:30  
> 狀態：📋 規劃中  
> 風險等級：🟡 中等

---

## 📊 分析結果

### 發現的過長函數

| 函數 | 行數 | 位置 | 優先級 | 複雜度 |
|------|------|------|--------|--------|
| `main()` | **635** | 1933-2567 | 🔴 最高 | 極高 |
| `_process_hybrid_pdf()` | **329** | 975-1303 | 🔴 高 | 高 |
| `_process_translation_on_pdf()` | **216** | 1620-1835 | 🟡 中 | 中 |
| `process_structured()` | **166** | 429-594 | 🟡 中 | 中 |
| `process_pdf()` | **122** | 596-717 | 🟢 低 | 中 |

**總計**：5 個函數超過 100 行，佔專案 **1,468 行**（56% 的程式碼！）

---

## 🎯 重構目標

### 主要目標

1. **`main()` 函數**：635 行 → **< 100 行**
2. **`_process_hybrid_pdf()`**：329 行 → **< 150 行**
3. **其他過長函數**：各自 < 100 行

### 成功指標

- ✅ 所有函數 < 100 行（`main` 除外，目標 < 100 行）
- ✅ 平均函數長度 < 50 行
- ✅ 測試覆蓋率不降低（維持 80%）
- ✅ 所有現有測試通過

---

## 📋 Task 2.1: 重構 `main()` 函數

### 當前問題

**`main()` 函數（635 行）包含**：

1. ArgumentParser 設定（~200 行）
2. 參數驗證和設定（~100 行）
3. 模式分發邏輯（~150 行）
4. 輸出路徑處理（~100 行）
5. 錯誤處理（~85 行）

### 重構策略：提取子模組

#### 新增檔案結構

```
paddleocr_toolkit/
└── cli/
    ├── __init__.py
    ├── argument_parser.py      # ArgumentParser 設定
    ├── config_handler.py        # 設定檔處理
    └── output_manager.py        # 輸出路徑管理
```

#### 重構步驟

**Step 1: 提取 ArgumentParser（~200 行）**

```python
# paddleocr_toolkit/cli/argument_parser.py

def create_argument_parser() -> argparse.ArgumentParser:
    """建立命令列參數解析器
    
    Returns:
        argparse.ArgumentParser: 設定好的參數解析器
    """
    parser = argparse.ArgumentParser(...)
    
    # 基本參數
    parser.add_argument("input", ...)
    
    # OCR 模式
    parser.add_argument("--mode", ...)
    
    # ... 所有參數設定
    
    return parser
```

**預期減少**：main() 從 635 行 → **435 行**

---

**Step 2: 提取輸出路徑管理（~100 行）**

```python
# paddleocr_toolkit/cli/output_manager.py

class OutputPathManager:
    """管理輸出檔案路徑"""
    
    def __init__(self, input_path: str, mode: str):
        self.input_path = input_path
        self.mode = mode
        self.base_name = Path(input_path).stem
    
    def get_searchable_pdf_path(self, custom_output: Optional[str] = None) -> str:
        """取得可搜尋 PDF 路徑"""
        if custom_output:
            return custom_output
        return f"{self.base_name}_searchable.pdf"
    
    def get_text_output_path(self, custom_output: Optional[str] = None) -> str:
        """取得文字輸出路徑"""
        if custom_output == 'AUTO':
            return f"{self.base_name}_ocr.txt"
        return custom_output
    
    # ... 其他輸出路徑方法
```

**預期減少**：main() 從 435 行 → **335 行**

---

**Step 3: 提取設定檔處理（~50 行）**

```python
# paddleocr_toolkit/cli/config_handler.py

def load_and_merge_config(
    args: argparse.Namespace,
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """載入設定檔並與 CLI 參數合併
    
    Args:
        args: 命令列參數
        config_path: 設定檔路徑（可選）
    
    Returns:
        Dict[str, Any]: 合併後的設定
    """
    config = {}
    
    if config_path:
        config = load_config(config_path)
    
    # CLI 參數覆蓋設定檔
    if args.mode:
        config['mode'] = args.mode
    
    # ...
    
    return config
```

**預期減少**：main() 從 335 行 → **285 行**

---

**Step 4: 提取模式分發邏輯（~150 行）**

```python
# paddleocr_toolkit/cli/mode_dispatcher.py

class ModeDispatcher:
    """OCR 模式分發器"""
    
    def __init__(self, tool: PaddleOCRTool, output_manager: OutputPathManager):
        self.tool = tool
        self.output_manager = output_manager
    
    def dispatch(self, mode: str, input_path: str, **kwargs) -> Dict[str, Any]:
        """根據模式分發處理
        
        Args:
            mode: OCR 模式
            input_path: 輸入檔案路徑
            **kwargs: 其他參數
        
        Returns:
            Dict[str, Any]: 處理結果
        """
        if mode == "basic":
            return self._handle_basic_mode(input_path, **kwargs)
        elif mode == "structure":
            return self._handle_structure_mode(input_path, **kwargs)
        elif mode == "hybrid":
            return self._handle_hybrid_mode(input_path, **kwargs)
        # ...
    
    def _handle_basic_mode(self, input_path: str, **kwargs):
        """處理 basic 模式"""
        # ...
    
    def _handle_hybrid_mode(self, input_path: str, **kwargs):
        """處理 hybrid 模式"""
        # ...
```

**預期減少**：main() 從 285 行 → **< 135 行**

---

**Step 5: 簡化後的 `main()` 函數**

```python
# paddle_ocr_tool.py

def main():
    """命令列入口點"""
    # 解析參數
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # 載入設定
    config = load_and_merge_config(args, args.config)
    
    # 驗證輸入
    if not os.path.exists(args.input):
        print(f"錯誤：找不到檔案 {args.input}")
        sys.exit(1)
    
    # 初始化工具
    tool = PaddleOCRTool(
        mode=config.get('mode', 'basic'),
        # ... 其他參數
    )
    
    # 建立輸出管理器
    output_manager = OutputPathManager(args.input, config['mode'])
    
    # 分發到對應模式
    dispatcher = ModeDispatcher(tool, output_manager)
    result = dispatcher.dispatch(
        mode=config['mode'],
        input_path=args.input,
        **config
    )
    
    # 顯示結果
    print_result_summary(result)
```

**最終目標**：main() **< 100 行** ✅

---

## 📋 Task 2.2: 重構 `_process_hybrid_pdf()`

### 當前問題

**`_process_hybrid_pdf()` 函數（329 行）包含**：

1. PDF 初始化（~30 行）
2. 準備生成器和工具（~40 行）
3. 主處理循環（~200 行）
   - 版面分析
   - OCR 提取
   - PDF 生成
   - 擦除處理
4. 輸出處理（~60 行）
   - Markdown
   - JSON
   - HTML

### 重構策略：提取子方法

**Step 1: 提取初始化邏輯**

```python
def _setup_hybrid_generators(
    self, 
    output_path: str, 
    erased_output_path: str
) -> Tuple[PDFGenerator, PDFGenerator, TextInpainter]:
    """設定混合模式所需的生成器
    
    Returns:
        Tuple of (pdf_generator, erased_generator, inpainter)
    """
    pdf_generator = PDFGenerator(
        output_path,
        debug_mode=self.debug_mode,
        compress_images=self.compress_images,
        jpeg_quality=self.jpeg_quality
    )
    
    erased_generator = PDFGenerator(
        erased_output_path,
        debug_mode=self.debug_mode,
        compress_images=self.compress_images,
        jpeg_quality=self.jpeg_quality
    )
    
    inpainter = TextInpainter() if HAS_TRANSLATOR else None
    
    return pdf_generator, erased_generator, inpainter
```

---

**Step 2: 提取單頁處理邏輯**

```python
def _process_single_page_hybrid(
    self,
    page,
    page_num: int,
    dpi: int,
    pdf_generator: PDFGenerator,
    erased_generator: PDFGenerator,
    inpainter: Optional[TextInpainter]
) -> Tuple[str, List[OCRResult]]:
    """處理單一頁面（混合模式）
    
    Args:
        page: PyMuPDF 頁面物件
        page_num: 頁碼
        dpi: 解析度
        pdf_generator: PDF 生成器
        erased_generator: 擦除版生成器
        inpainter: 文字擦除器
    
    Returns:
        Tuple of (page_markdown, ocr_results)
    """
    # 轉換為圖片
    img_array = self._page_to_image(page, dpi)
    
    # 版面分析
    structure_output = self.structure_engine.predict(input=img_array)
    
    # 提取 Markdown
    page_markdown = self._extract_markdown_from_structure(
        structure_output, page_num
    )
    
    # 提取 OCR 結果
    ocr_results = self._extract_ocr_from_structure(
        structure_output, page_markdown
    )
    
    # 生成 PDFs
    self._generate_dual_pdfs(
        img_array,
        ocr_results,
        pdf_generator,
        erased_generator,
        inpainter
    )
    
    return page_markdown, ocr_results
```

---

**Step 3: 提取輸出處理**

```python
def _save_hybrid_outputs(
    self,
    all_markdown: List[str],
    all_ocr_results: List[List[OCRResult]],
    markdown_output: Optional[str],
    json_output: Optional[str],
    html_output: Optional[str],
    pdf_path: str
) -> Dict[str, str]:
    """儲存混合模式的各種輸出
    
    Returns:
        Dict of output paths
    """
    outputs = {}
    
    if markdown_output:
        outputs['markdown'] = self._save_markdown(
            all_markdown, markdown_output
        )
    
    if json_output:
        outputs['json'] = self._save_json(
            all_ocr_results, json_output, pdf_path
        )
    
    if html_output:
        outputs['html'] = self._save_html(
            all_markdown, html_output, pdf_path
        )
    
    return outputs
```

---

**Step 4: 簡化後的 `_process_hybrid_pdf()`**

```python
def _process_hybrid_pdf(
    self,
    pdf_path: str,
    output_path: str,
    markdown_output: str,
    json_output: Optional[str],
    html_output: Optional[str],
    dpi: int,
    show_progress: bool,
    result_summary: Dict[str, Any],
    translate_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """處理 PDF 的混合模式"""
    
    # 初始化
    pdf_doc = fitz.open(pdf_path)
    total_pages = len(pdf_doc)
    
    # 設定生成器
    erased_output_path = output_path.replace('_hybrid.pdf', '_erased.pdf')
    pdf_gen, erased_gen, inpainter = self._setup_hybrid_generators(
        output_path, erased_output_path
    )
    
    # 初始化統計
    stats = StatsCollector(pdf_path, "hybrid", total_pages)
    
    # 處理所有頁面
    all_markdown, all_ocr_results = self._process_all_pages(
        pdf_doc,
        total_pages,
        dpi,
        pdf_gen,
        erased_gen,
        inpainter,
        stats,
        show_progress
    )
    
    pdf_doc.close()
    
    # 儲存 PDFs
    pdf_gen.save()
    erased_gen.save()
    
    # 儲存其他輸出
    outputs = self._save_hybrid_outputs(
        all_markdown,
        all_ocr_results,
        markdown_output,
        json_output,
        html_output,
        pdf_path
    )
    
    # 翻譯處理（如果啟用）
    if translate_config and HAS_TRANSLATOR and not self.debug_mode:
        self._process_translation_on_pdf(
            erased_output_path,
            all_ocr_results,
            translate_config,
            result_summary,
            dpi
        )
    
    # 完成統計
    final_stats = stats.finish()
    final_stats.print_summary()
    
    result_summary.update({
        "pages_processed": total_pages,
        "stats": final_stats.to_dict(),
        **outputs
    })
    
    return result_summary
```

**最終目標**：`_process_hybrid_pdf()` **< 150 行** ✅

---

## 📋 Task 2.3: 提取重複邏輯

### 識別的重複模式

#### 1. 路徑處理重複

**出現位置**：多處  
**問題**：相同的路徑驗證和規範化邏輯

```python
# 重複出現的模式
if not os.path.exists(path):
    print(f"錯誤：找不到檔案 {path}")
    return False

# 或
input_path = Path(input).resolve()
base_name = input_path.stem
```

**解決方案**：建立 `path_utils.py`

```python
# paddleocr_toolkit/utils/path_utils.py

def validate_input_path(path: str) -> Path:
    """驗證並規範化輸入路徑
    
    Args:
        path: 輸入路徑
    
    Returns:
        Path: 規範化的 Path 物件
    
    Raises:
        FileNotFoundError: 檔案不存在時
    """
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"找不到檔案：{path}")
    return p

def get_output_path(
    input_path: str,
    suffix: str,
    custom_output: Optional[str] = None
) -> str:
    """產生輸出檔案路徑
    
    Args:
        input_path: 輸入檔案路徑
        suffix: 後綴（如 '_ocr.txt'）
        custom_output: 自訂輸出路徑（可選）
    
    Returns:
        str: 輸出檔案路徑
    """
    if custom_output:
        return custom_output
    
    base = Path(input_path).stem
    return f"{base}{suffix}"
```

---

#### 2. 錯誤訊息格式化重複

**出現位置**：多處  
**問題**：類似的錯誤訊息格式

```python
# 重複模式
logging.error(f"處理第 {page_num + 1} 頁時發生錯誤: {error}")
logging.error(traceback.format_exc())

# 或
print(f"錯誤：{error}")
```

**解決方案**：統一錯誤處理

```python
# paddleocr_toolkit/utils/error_handler.py

def log_page_error(page_num: int, error: Exception):
    """記錄頁面處理錯誤
    
    Args:
        page_num: 頁碼（0-indexed）
        error: 異常物件
    """
    logging.error(f"處理第 {page_num + 1} 頁時發生錯誤: {error}")
    logging.error(traceback.format_exc())

def handle_file_error(file_path: str, error: Exception) -> None:
    """處理檔案錯誤
    
    Args:
        file_path: 檔案路徑
        error: 異常物件
    """
    print(f"錯誤：無法處理檔案 {file_path}")
    logging.error(f"檔案處理失敗: {file_path} - {error}")
    logging.error(traceback.format_exc())
```

---

#### 3. 進度顯示重複

**出現位置**：多個處理函數  
**問題**：相同的 tqdm 初始化邏輯

```python
# 重複模式
if show_progress and HAS_TQDM:
    iterator = tqdm(iterator, desc="處理中", unit="頁", ncols=80)
```

**解決方案**：統一進度管理

```python
# paddleocr_toolkit/utils/progress.py

def create_progress_bar(
    iterable,
    total: int,
    desc: str,
    show_progress: bool = True,
    unit: str = "項"
):
    """建立進度條
    
    Args:
        iterable: 可迭代物件
        total: 總數
        desc: 描述文字
        show_progress: 是否顯示進度
        unit: 單位
    
    Returns:
        進度條包裝的迭代器（或原迭代器）
    """
    if show_progress and HAS_TQDM:
        return tqdm(iterable, total=total, desc=desc, unit=unit, ncols=80)
    return iterable
```

---

## 📅 執行時間表

### Week 1（3-4 天）

**Day 1-2**: Task 2.1 - 重構 `main()`

- 建立 CLI 子模組
- 提取 ArgumentParser
- 提取輸出管理器
- 測試驗證

**Day 3-4**: Task 2.2 - 重構 `_process_hybrid_pdf()`

- 提取子方法
- 重構主邏輯
- 測試驗證

### Week 2（1-2 天）

**Day 5-6**: Task 2.3 - 提取重複邏輯

- 建立 utils 模組
- 替換重複程式碼
- 測試驗證

---

## ✅ 檢查清單

### 每個任務開始前

- [ ] 建立詳細實作計畫
- [ ] 確認所有測試通過
- [ ] 記錄當前覆蓋率（80%）

### 執行中

- [ ] 遵循 Artifact-First 原則
- [ ] 小步提交（每個子任務一次提交）
- [ ] 保持測試綠燈
- [ ] 更新相關文件

### 完成後

- [ ] 所有測試通過
- [ ] 覆蓋率 ≥ 80%
- [ ] 更新 `architecture.md`
- [ ] 更新 `README.md`（如有 API 變更）

---

## 🎯 預期成果

### 量化指標

- ✅ `main()`: 635 行 → **< 100 行**
- ✅ `_process_hybrid_pdf()`: 329 行 → **< 150 行**
- ✅ 平均函數長度 < 50 行
- ✅ 測試覆蓋率維持 80%

### 質化指標

- ✅ 程式碼更模組化
- ✅ 更易於測試
- ✅ 更易於維護
- ✅ 更易於擴展新功能

---

*計畫建立：2024-12-13 23:30*  
*預計開始：待用戶確認*  
*預計完成：5-7 天*
