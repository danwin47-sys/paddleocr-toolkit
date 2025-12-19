# Task 2.2: 重構 `_process_hybrid_pdf()` 實作計劃

> 建立時間：2024-12-14 07:05  
> 狀態：📋 計劃中  
> 風險等級：🟡 中等  
> 預計時間：1-1.5 小時

---

## 🎯 目標

重構 `_process_hybrid_pdf()` 方法（329 行，975-1303），將其簡化為 < 150 行。

**當前狀態**: 329 行  
**目標**: < 150 行（減少約 180 行，55% reduction）

---

## 📊 現狀分析

### `_process_hybrid_pdf()` 方法結構（975-1303，329 行）

#### 1. **初始化階段**（~30 行）

- 開啟 PDF（1000-1004）
- 設定輸出路徑（1006-1007）
- 準備 PDF 生成器（1009-1027）
- 初始化變數和統計（1029-1043）

#### 2. **主處理迴圈**（~120 行，1045-1170）

- 頁面迭代 + 進度條（1045）
- 單頁處理邏輯：
  - 轉換為圖片（1052-1058）
  - 版面分析（1060-1103）
  - 提取 OCR 座標（1105-1113）
  - 生成雙 PDF（1115-1145）
  - 收集結果（1147-1160）
  - 記憶體清理（1162-1164）
- 錯誤處理（1166-1169）

#### 3. **輸出儲存階段**（~100 行，1171-1278）

- 關閉 PDF（1171）
- 儲存可搜尋 PDF（1173-1176）
- 儲存擦除版 PDF（1178-1181）
- 儲存 Markdown（1183-1190）
- 儲存 JSON（1192-1219，28 行）
- 儲存 HTML（1221-1277，57 行）

#### 4. **後處理階段**（~20 行，1279-1303）

- 翻譯處理（1281-1294）
- 統計彙總（1296-1301）
- 返回結果（1303）

---

## 📋 重構策略

### 策略：提取 4 個私有方法

#### 方法 1: `_setup_hybrid_generators()` - 初始化生成器

**提取**: 1009-1027 (19 行)  
**新方法**: ~25 行

```python
def _setup_hybrid_generators(
    self,
    output_path: str
) -> Tuple[PDFGenerator, PDFGenerator, Optional[TextInpainter], str]:
    """設定混合模式所需的生成器
    
    Returns:
        Tuple of (pdf_generator, erased_generator, inpainter, erased_path)
    """
    erased_output_path = output_path.replace('_hybrid.pdf', '_erased.pdf')
    
    # 原文可搜尋 PDF
    pdf_generator = PDFGenerator(
        output_path,
        debug_mode=self.debug_mode,
        compress_images=self.compress_images,
        jpeg_quality=self.jpeg_quality
    )
    
    # 擦除版 PDF
    erased_generator = PDFGenerator(
        erased_output_path,
        debug_mode=self.debug_mode,
        compress_images=self.compress_images,
        jpeg_quality=self.jpeg_quality
    )
    
    # 擦除器
    inpainter = Text Inpainter() if HAS_TRANSLATOR else None
    
    logging.info(f"[DEBUG] PDFGenerator compress_images={pdf_generator.compress_images}")
    
    return pdf_generator, erased_generator, inpainter, erased_output_path
```

---

#### 方法 2: `_process_single_hybrid_page()` - 處理單頁

**提取**: 1050-1160 (110 行主迴圈內容)  
**新方法**: ~60 行

```python
def _process_single_hybrid_page(
    self,
    page,
    page_num: int,
    dpi: int,
    pdf_generator: PDFGenerator,
    erased_generator: PDFGenerator,
    inpainter: Optional[TextInpainter]
) -> Tuple[str, str, List[OCRResult]]:
    """處理單一頁面（混合模式）
    
    Returns:
        Tuple of (page_markdown, page_text, ocr_results)
    """
    # 轉換為圖片
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    img_array = pixmap_to_numpy(pixmap)
    
    # 版面分析
    structure_output = self.structure_engine.predict(input=img_array)
    
    # 提取 Markdown
    page_markdown = self._extract_markdown_from_structure_output(
        structure_output, page_num
    )
    
    # 提取 OCR 座標
    sorted_results = self._extract_ocr_from_structure(
        structure_output, markdown_text=page_markdown
    )
    
    # 生成雙 PDF
    if sorted_results:
        self._generate_dual_pdfs(
            pixmap, img_array, sorted_results,
            pdf_generator, erased_generator, inpainter
        )
    
    # 提取文字
    page_text = self.get_text(sorted_results)
    
    # 清理
    del pixmap
    gc.collect()
    
    return page_markdown, page_text, sorted_results
```

---

#### 方法 3: `_save_hybrid_outputs()` - 儲存輸出檔案

**提取**: 1183-1278 (96 行)  
**新方法**: ~50 行

```python
def _save_hybrid_outputs(
    self,
    all_markdown: List[str],
    all_ocr_results: List[List[OCRResult]],
    markdown_output: Optional[str],
    json_output: Optional[str],
    html_output: Optional[str],
    pdf_path: str,
    result_summary: Dict[str, Any]
) -> None:
    """儲存混合模式的各種輸出檔案"""
    
    # 儲存 Markdown
    if markdown_output and all_markdown:
        self._save_markdown_output(all_markdown, markdown_output, result_summary)
    
    # 儲存 JSON
    if json_output:
        self._save_json_output(all_ocr_results, json_output, pdf_path, result_summary)
    
    # 儲存 HTML
    if html_output:
        self._save_html_output(all_markdown, html_output, pdf_path, result_summary)
```

---

#### 方法 4: `_extract_markdown_from_structure_output()` - 提取 Markdown

**提取**: 1065-1083 (19 行)  
**新方法**: ~25 行

```python
def _extract_markdown_from_structure_output(
    self,
    structure_output,
    page_num: int
) -> str:
    """從 PP-StructureV3 輸出提取 Markdown
    
    Returns:
        str: 頁面的 Markdown 文字
    """
    page_markdown = f"## 第 {page_num + 1} 頁\n\n"
    
    for res in structure_output:
        temp_md_dir = tempfile.mkdtemp()
        try:
            if hasattr(res, 'save_to_markdown'):
                res.save_to_markdown(save_path=temp_md_dir)
                for md_file in Path(temp_md_dir).glob("*.md"):
                    with open(md_file, 'r', encoding='utf-8') as f:
                        page_markdown += f.read()
                    break
        except Exception as md_err:
            logging.warning(f"save_to_markdown 失敗: {md_err}")
            if hasattr(res, 'markdown') and isinstance(res.markdown, str):
                page_markdown += res.markdown
        finally:
            shutil.rmtree(temp_md_dir, ignore_errors=True)
    
    return page_markdown
```

---

#### 方法 5: `_generate_dual_pdfs()` - 生成雙 PDF

**提取**: 1116-1145 (30 行)  
**新方法**: ~35 行

```python
def _generate_dual_pdfs(
    self,
    pixmap,
    img_array: np.ndarray,
    sorted_results: List[OCRResult],
    pdf_generator: PDFGenerator,
    erased_generator: PDFGenerator,
    inpainter: Optional[TextInpainter]
) -> None:
    """生成原文 PDF 和擦除版 PDF"""
    
    img_array_copy = img_array.copy()
    
    # 1. 原文可搜尋 PDF
    pdf_generator.add_page_from_pixmap(pixmap, sorted_results)
    
    # 2. 擦除版 PDF
    if inpainter:
        bboxes = [
            result.bbox 
            for result in sorted_results 
            if result.text and result.text.strip()
        ]
        
        if bboxes:
            erased_image = inpainter.erase_multiple_regions(
                img_array_copy, bboxes, fill_color=(255, 255, 255)
            )
        else:
            erased_image = img_array_copy
        
        # 儲存到臨時檔案並新增
        tmp_erased_path = tempfile.mktemp(suffix='.png')
        try:
            Image.fromarray(erased_image).save(tmp_erased_path)
            erased_generator.add_page(tmp_erased_path, sorted_results)
        finally:
            if os.path.exists(tmp_erased_path):
                os.remove(tmp_erased_path)
```

---

### 額外方法（輸出儲存輔助）

#### 方法 6: `_save_markdown_output()` - 儲存 Markdown

```python
def _save_markdown_output(
    self,
    all_markdown: List[str],
    markdown_output: str,
    result_summary: Dict[str, Any]
) -> None:
    """儲存 Markdown 輸出"""
    fixed_markdown = [fix_english_spacing(md) for md in all_markdown]
    with open(markdown_output, 'w', encoding='utf-8') as f:
        f.write("\n\n---\n\n".join(fixed_markdown))
    result_summary["markdown_file"] = markdown_output
    print(f"[OK] Markdown 已儲存：{markdown_output}")
```

#### 方法 7: `_save_json_output()` - 儲存 JSON

```python
def _save_json_output(
    self,
    all_ocr_results: List[List[OCRResult]],
    json_output: str,
    pdf_path: str,
    result_summary: Dict[str, Any]
) -> None:
    """儲存 JSON 輸出"""
    # JSON 序列化邏輯（28 行）
```

#### 方法 8: `_save_html_output()` - 儲存 HTML

```python
def _save_html_output(
    self,
    all_markdown: List[str],
    html_output: str,
    pdf_path: str,
    result_summary: Dict[str, Any]
) -> None:
    """儲存 HTML 輸出"""
    # HTML 生成邏輯（57 行）
```

---

## 📊 重構後的 `_process_hybrid_pdf()`

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
    
    # === 1. 初始化 ===
    pdf_doc = fitz.open(pdf_path)
    total_pages = len(pdf_doc)
    print(f"PDF 共 {total_pages} 頁")
    
    # 設定生成器
    pdf_gen, erased_gen, inpainter, erased_path = self._setup_hybrid_generators(output_path)
    
    # 初始化收集器
    all_markdown, all_text, all_ocr_results = [], [], []
    stats = StatsCollector(pdf_path, "hybrid", total_pages)
    
    # === 2. 處理所有頁面 ===
    page_iterator = range(total_pages)
    if show_progress and HAS_TQDM:
        page_iterator = tqdm(page_iterator, desc="混合模式處理中", unit="頁")
    
    for page_num in page_iterator:
        try:
            stats.start_page(page_num)
            page = pdf_doc[page_num]
            
            # 處理單頁
            page_md, page_txt, ocr_res = self._process_single_hybrid_page(
                page, page_num, dpi, pdf_gen, erased_gen, inpainter
            )
            
            # 收集結果
            all_markdown.append(page_md)
            all_text.append(page_txt)
            all_ocr_results.append(ocr_res)
            
            result_summary["pages_processed"] += 1
            stats.finish_page(page_num, page_txt, ocr_res)
            
        except Exception as e:
            logging.error(f"處理第 {page_num + 1} 頁錯誤: {e}")
            continue
    
    pdf_doc.close()
    
    # === 3. 儲存 PDF ===
    if pdf_gen.save():
        result_summary["searchable_pdf"] = output_path
        print(f"[OK] 可搜尋 PDF 已儲存：{output_path}")
    
    if erased_gen.save():
        result_summary["erased_pdf"] = erased_path
        print(f"[OK] 擦除版 PDF 已儲存：{erased_path}")
    
    # === 4. 儲存其他輸出 ===
    self._save_hybrid_outputs(
        all_markdown, all_ocr_results,
        markdown_output, json_output, html_output,
        pdf_path, result_summary
    )
    
    result_summary["text_content"] = all_text
    
    # === 5. 翻譯處理 ===
    if translate_config and HAS_TRANSLATOR and not self.debug_mode:
        self._process_translation_on_pdf(
            erased_path, all_ocr_results, translate_config,
            result_summary, dpi
        )
    
    # === 6. 完成統計 ===
    print(f"[OK] 混合模式處理完成：{result_summary['pages_processed']} 頁")
    final_stats = stats.finish()
    final_stats.print_summary()
    result_summary["stats"] = final_stats.to_dict()
    
    return result_summary
```

**重構後行數**: ~80 行

---

## 📊 預期成果

### 程式碼行數變化

| 專案 | 原始 | 重構後 | 減少 |
|------|------|--------|------|
| `_process_hybrid_pdf()` | 329 | **~80** | **-249** (-76%) |
| 新增方法 | 0 | **~260** | +260 |
| **淨變化** | 329 | **340** | **+11** |

### 程式碼質量提升

- ✅ **主方法簡化**: 329 → 80 行 (76% reduction)
- ✅ **職責分離**: 每個方法單一職責
- ✅ **可測試性**: 每個子方法可獨立測試
- ✅ **可讀性**: 清晰的步驟結構
- ✅ **可維護性**: 易於修改和擴充套件

---

## 📋 執行步驟

### Step 1: 提取初始化和生成器設定

- 建立 `_setup_hybrid_generators()`
- 建立 `_extract_markdown_from_structure_output()`
- 建立 `_generate_dual_pdfs()`

### Step 2: 提取單頁處理邏輯

- 建立 `_process_single_hybrid_page()`

### Step 3: 提取輸出儲存邏輯

- 建立 `_save_markdown_output()`
- 建立 `_save_json_output()`
- 建立 `_save_html_output()`
- 建立 `_save_hybrid_outputs()`（統籌方法）

### Step 4: 簡化主方法

- 重寫 `_process_hybrid_pdf()` 使用新方法

### Step 5: 測試驗證

- 執行現有測試
- 測試各種模式

---

## ⚠️ 注意事項

### 需要保持的功能

1. ✅ 雙 PDF 生成（原文 + 擦除版）
2. ✅ 多種輸出格式（MD/JSON/HTML）
3. ✅ 翻譯功能整合
4. ✅ 統計收集
5. ✅ 記憶體管理

### 風險點

1. **記憶體管理**: 確保 pixmap 正確釋放
2. **臨時檔案**: 確保清理
3. **錯誤處理**: 保持健壯性
4. **翻譯整合**: 不破壞現有翻譯功能

---

## 🎯 成功標準

- ✅ `_process_hybrid_pdf()` < 100 行
- ✅ 新增 8 個結構清晰的私有方法
- ✅ 所有測試透過
- ✅ hybrid 模式功能完全保留
- ✅ 翻譯功能正常工作

---

## 💡 建議

**考慮到時間（現在 07:05）和任務複雜度**：

### 選項 A: 稍後執行（推薦）

- 這是個較大的重構（預計 1-1.5 小時）
- 已經工作了 30+ 分鐘
- 可以稍後精力充沛時執行

### 選項 B: 立即執行

- 如果精力充沛可以繼續
- 採用分步測試策略
- 預計 1-1.5 小時

---

*計劃建立：2024-12-14 07:05*  
*預計執行時間：1-1.5 小時*  
*難度：🟡 中等*  
*優先順序：🟡 中*
