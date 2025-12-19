# Task 2.3: 重構 _process_translation_on_pdf() 實作計劃

> 建立時間：2024-12-14 07:26  
> 狀態：📋 計劃中  
> 風險等級：🔴 高  
> 預計時間：1-1.5 小時

---

## 🎯 目標

重構 `_process_translation_on_pdf()` 方法（217 行，1761-1977），將其簡化為 < 100 行。

**當前狀態**: 217 行  
**目標**: < 100 行（減少約 120 行，55% reduction）

---

## 📊 現狀分析

### `_process_translation_on_pdf()` 方法結構（1761-1977，217 行）

#### 1. **初始化階段**（~45 行，1785-1830）

- 提取配置引數（source_lang, target_lang等）
- 初始化 translator 和 renderer
- 開啟 PDF 檔案
- 建立輸出路徑
- 建立 PDF 生成器

#### 2. **主處理迴圈**（~105 行，1837-1949）

- 頁面迭代 + 進度條
- 單頁處理邏輯：
  - 獲取 OCR 結果
  - 轉換為圖片
  - 翻譯文字
  - 繪製翻譯文字（標準模式 vs OCR workaround）
  - 新增到 PDF 生成器
- 錯誤處理

#### 3. **儲存輸出階段**（~20 行，1951-1970）

- 關閉PDF檔案
- 儲存翻譯版 PDF
- 儲存雙語版 PDF

#### 4. **錯誤處理**（~7 行，1971-1976）

---

## 📋 重構策略

### 策略：提取 6 個私有方法

#### 方法 1: `_setup_translation_tools()` - 初始化翻譯工具

**提取**: 1806-1830 (25 行)  
**新方法**: ~35 行

```python
def _setup_translation_tools(
    self,
    erased_pdf_path: str,
    translate_config: Dict[str, Any]
) -> Tuple:
    """設定翻譯所需的工具和生成器
    
    Returns:
        Tuple of (translator,  renderer, pdf_doc, hybrid_doc,
                  mono_generator, bilingual_generator, 
                  translated_path, bilingual_path)
    """
    # 初始化翻譯器和繪製器
    translator = OllamaTranslator(
        model=translate_config['ollama_model'],
        base_url=translate_config['ollama_url']
    )
    renderer = TextRenderer(font_path=translate_config.get('font_path'))
    
    # 開啟PDF
    pdf_doc = fitz.open(erased_pdf_path)
    
    # 開啟原始hybrid PDF（用於雙語）
    hybrid_pdf_path = erased_pdf_path.replace('_erased.pdf', '_hybrid.pdf')
    hybrid_doc = None
    if not translate_config['no_dual'] and os.path.exists(hybrid_pdf_path):
        hybrid_doc = fitz.open(hybrid_pdf_path)
    
    # 建立輸出路徑
    base_path = erased_pdf_path.replace('_erased.pdf', '')
    target_lang = translate_config['target_lang']
    translated_path = f"{base_path}_translated_{target_lang}.pdf" \
        if not translate_config['no_mono'] else None
    bilingual_path = f"{base_path}_bilingual_{target_lang}.pdf" \
        if not translate_config['no_dual'] else None
    
    # 建立生成器
    mono_generator = MonolingualPDFGenerator() if translated_path else None
    bilingual_generator = BilingualPDFGenerator(
        mode=translate_config['dual_mode'],
        translate_first=translate_config.get('dual_translate_first', False)
    ) if bilingual_path else None
    
    return (translator, renderer, pdf_doc, hybrid_doc,
            mono_generator, bilingual_generator, 
            translated_path, bilingual_path)
```

---

#### 方法 2: `_get_page_images()` - 獲取頁面圖片

**提取**: 1846-1860 (15 行)  
**新方法**: ~20 行

```python
def _get_page_images(
    self,
    pdf_doc,
    hybrid_doc: Optional,
    page_num: int,
    dpi: int
) -> Tuple[np.ndarray, np.ndarray]:
    """獲取擦除版和原始版頁面圖片
    
    Returns:
        Tuple of (erased_image, original_image)
    """
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    
    # 獲取擦除版圖片
    erased_page = pdf_doc[page_num]
    erased_pixmap = erased_page.get_pixmap(matrix=matrix)
    erased_image = pixmap_to_numpy(erased_pixmap, copy=True)
    
    # 獲取原始圖片（用於雙語）
    original_image = erased_image.copy()
    if hybrid_doc:
        hybrid_page = hybrid_doc[page_num]
        hybrid_pixmap = hybrid_page.get_pixmap(matrix=matrix)
        original_image = pixmap_to_numpy(hybrid_pixmap, copy=True)
    
    return erased_image, original_image
```

---

#### 方法 3: `_translate_page_texts()` - 翻譯頁面文字

**提取**: 1870-1901 (32 行)  
**新方法**: ~25 行

```python
def _translate_page_texts(
    self,
    page_ocr_results: List[OCRResult],
    translator,
    source_lang: str,
    target_lang: str,
    page_num: int
) -> List[TranslatedBlock]:
    """翻譯頁面的所有文字
    
    Returns:
        List[TranslatedBlock]: 翻譯後的文字塊列表
    """
    # 收集需要翻譯的文字
    texts_to_translate = []
    bboxes = []
    for result in page_ocr_results:
        if result.text and result.text.strip():
            texts_to_translate.append(result.text)
            bboxes.append(result.bbox)
    
    if not texts_to_translate:
        return []
    
    logging.info(f"第 {page_num + 1} 頁: 翻譯 {len(texts_to_translate)} 個文字區塊")
    
    # 批次翻譯
    translated_texts = translator.translate_batch(
        texts_to_translate, source_lang, target_lang, show_progress=False
    )
    
    # 建立 TranslatedBlock 列表
    translated_blocks = []
    for orig, trans, bbox in zip(texts_to_translate, translated_texts, bboxes):
        translated_blocks.append(TranslatedBlock(
            original_text=orig,
            translated_text=trans,
            bbox=bbox
        ))
    
    return translated_blocks
```

---

#### 方法 4: `_render_translated_text()` - 繪製翻譯文字

**提取**: 1903-1932 (30 行)  
**新方法**: ~35 行

```python
def _render_translated_text(
    self,
    erased_image: np.ndarray,
    erased_page,  # PyMuPDF page object
    translated_blocks: List[TranslatedBlock],
    renderer: TextRenderer,
    use_ocr_workaround: bool,
    dpi: int
) -> np.ndarray:
    """在擦除版圖片上繪製翻譯文字
    
    Returns:
        np.ndarray: 繪製了翻譯文字的圖片
    """
    if use_ocr_workaround:
        # OCR 補救模式：直接在 PDF 頁面上操作
        logging.info("使用 OCR 補救模式繪製翻譯文字")
        workaround = OCRWorkaround(margin=2.0, force_black=True)
        
        for block in translated_blocks:
            # 計算座標
            x = min(p[0] for p in block.bbox)
            y = min(p[1] for p in block.bbox)
            width = max(p[0] for p in block.bbox) - x
            height = max(p[1] for p in block.bbox) - y
            
            text_block = TextBlock(
                text=block.translated_text,
                x=x, y=y, width=width, height=height
            )
            workaround.add_text_with_mask(erased_page, text_block, block.translated_text)
        
        # 從修改後的頁面獲取圖片
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        modified_pixmap = erased_page.get_pixmap(matrix=matrix)
        translated_image = pixmap_to_numpy(modified_pixmap, copy=True)
    else:
        # 標準模式：使用 TextRenderer
        translated_image = erased_image.copy()
        translated_image = renderer.render_multiple_texts(
            translated_image, translated_blocks
        )
    
    return translated_image
```

---

#### 方法 5: `_process_single_translation_page()` - 處理單頁翻譯

**提取**: 1838-1944 (107 行主迴圈內容)  
**新方法**: ~45 行

```python
def _process_single_translation_page(
    self,
    page_num: int,
    ocr_results_per_page: List[List[OCRResult]],
    pdf_doc,
    hybrid_doc: Optional,
    translator,
    renderer,
    mono_generator,
    bilingual_generator,
    translate_config: Dict[str, Any],
    dpi: int
) -> None:
    """處理單頁翻譯
    
    完整流程：獲取圖片 → 翻譯 → 繪製 → 新增到生成器
    """
    # 檢查 OCR 結果
    if page_num >= len(ocr_results_per_page):
        logging.warning(f"第 {page_num + 1} 頁沒有 OCR 結果")
        return
    
    page_ocr_results = ocr_results_per_page[page_num]
    
    # 獲取頁面圖片
    erased_image, original_image = self._get_page_images(
        pdf_doc, hybrid_doc, page_num, dpi
    )
    
    # 如果沒有 OCR 結果，直接新增空白頁
    if not page_ocr_results:
        if mono_generator:
            mono_generator.add_page(erased_image)
        if bilingual_generator:
            bilingual_generator.add_bilingual_page(original_image, erased_image)
        return
    
    # 翻譯文字
    translated_blocks = self._translate_page_texts(
        page_ocr_results, translator,
        translate_config['source_lang'],
        translate_config['target_lang'],
        page_num
    )
    
    # 如果沒有需要翻譯的文字
    if not translated_blocks:
        if mono_generator:
            mono_generator.add_page(erased_image)
        if bilingual_generator:
            bilingual_generator.add_bilingual_page(original_image, erased_image)
        return
    
    # 繪製翻譯文字
    erased_page = pdf_doc[page_num] if translate_config.get('ocr_workaround') else None
    translated_image = self._render_translated_text(
        erased_image, erased_page, translated_blocks,
        renderer, translate_config.get('ocr_workaround', False), dpi
    )
    
    # 新增到生成器
    if mono_generator:
        mono_generator.add_page(translated_image)
    if bilingual_generator:
        bilingual_generator.add_bilingual_page(original_image, translated_image  )
    
    # 清理
    gc.collect()
```

---

#### 方法 6: `_save_translation_pdfs()` - 儲存翻譯PDF

**提取**: 1955-1967 (13 行)  
**新方法**: ~20 行

```python
def _save_translation_pdfs(
    self,
    mono_generator,
    bilingual_generator,
    translated_path: Optional[str],
    bilingual_path: Optional[str],
    result_summary: Dict[str, Any]
) -> None:
    """儲存翻譯版和雙語版 PDF"""
    # 儲存翻譯版 PDF
    if mono_generator and translated_path:
        if mono_generator.save(translated_path):
            result_summary["translated_pdf"] = translated_path
            print(f"[OK] 翻譯 PDF 已儲存：{translated_path}")
        mono_generator.close()
    
    # 儲存雙語版 PDF
    if bilingual_generator and bilingual_path:
        if bilingual_generator.save(bilingual_path):
            result_summary["bilingual_pdf"] = bilingual_path
            print(f"[OK] 雙語對照 PDF 已儲存：{bilingual_path}")
        bilingual_generator.close()
```

---

## 📊 重構後的 `_process_translation_on_pdf()`

```python
def _process_translation_on_pdf(
    self,
    erased_pdf_path: str,
    ocr_results_per_page: List[List[OCRResult]],
    translate_config: Dict[str, Any],
    result_summary: Dict[str, Any],
    dpi: int = 150
) -> None:
    """在擦除版 PDF 基礎上進行翻譯處理"""
    
    print(f"\n[翻譯] 開始翻譯處理...")
    print(f"   來源語言: {translate_config['source_lang']}")
    print(f"   目標語言: {translate_config['target_lang']}")
    print(f"   Ollama 模型: {translate_config['ollama_model']}")
    
    try:
        # === 1. 初始化工具 ===
        (translator, renderer, pdf_doc, hybrid_doc,
         mono_gen, bilingual_gen, 
         trans_path, bi_path) = self._setup_translation_tools(
            erased_pdf_path, translate_config
        )
        
        total_pages = len(pdf_doc)
        
        # === 2. 處理所有頁面 ===
        page_iter = range(total_pages)
        if HAS_TQDM:
            page_iter = tqdm(page_iter, desc="翻譯頁面", unit="頁", ncols=80)
        
        for page_num in page_iter:
            try:
                self._process_single_translation_page(
                    page_num, ocr_results_per_page,
                    pdf_doc, hybrid_doc,
                    translator, renderer,
                    mono_gen, bilingual_gen,
                    translate_config, dpi
                )
            except Exception as page_err:
                logging.error(f"翻譯第 {page_num + 1} 頁錯誤: {page_err}")
                logging.error(traceback.format_exc())
                continue
        
        # === 3. 儲存輸出 ===
        pdf_doc.close()
        if hybrid_doc:
            hybrid_doc.close()
        
        self._save_translation_pdfs(
            mono_gen, bilingual_gen,
            trans_path, bi_path,
            result_summary
        )
        
        print(f"[OK] 翻譯處理完成")
        
    except Exception as e:
        error_msg = f"翻譯處理失敗: {str(e)}"
        logging.error(error_msg)
        logging.error(traceback.format_exc())
        print(f"錯誤：{error_msg}")
        result_summary["translation_error"] = str(e)
```

**重構後行數**: ~60 行

---

## 📊 預期成果

### 程式碼行數變化

| 專案 | 原始 | 重構後 | 減少 |
|------|------|--------|------|
| `_process_translation_on_pdf()` | 217 | **~60** | **-157** (-72%) |
| 新增方法 | 0 | **~180** | +180 |
| **淨變化** | 217 | **240** | **+23** |

### 程式碼質量提升

- ✅ **主方法簡化**: 217 → 60 行 (72% reduction)
- ✅ **職責分離**: 每個方法單一職責
- ✅ **可測試性**: 每個子方法可獨立測試
- ✅ **可讀性**: 清晰的3步驟結構
- ✅ **可維護性**: 易於修改和擴充套件

---

## 📋 執行步驟

### Step 1: 建立 6 個輔助方法

1. `_setup_translation_tools()`
2. `_get_page_images()`
3. `_translate_page_texts()`
4. `_render_translated_text()`
5. `_process_single_translation_page()`
6. `_save_translation_pdfs()`

### Step 2: 簡化主方法

- 重寫 `_process_translation_on_pdf()` 使用新方法

### Step 3: 測試驗證

- 執行現有測試
- 如果有翻譯測試，驗證功能

### Step 4: 提交 Git

---

## ⚠️ 注意事項

### 需要保持的功能

1. ✅ 雙模式翻譯（標準 vs OCR workaround）
2. ✅ 多種輸出（單語、雙語PDF）
3. ✅ 進度條顯示
4. ✅ 記憶體管理

### 風險點

1. **翻譯API呼叫**: 確保正確傳遞引數
2. **PDF操作**: PyMuPDF物件正確管理
3. **記憶體管理**: 及時釋放pixmap
4. **錯誤處理**: 保持健壯性

---

## 🎯 成功標準

- ✅ `_process_translation_on_pdf()` < 100 行
- ✅ 新增 6 個結構清晰的私有方法
- ✅ 所有測試透過
- ✅ 翻譯功能完全保留

---

*計劃建立：2024-12-14 07:26*  
*預計執行時間：1-1.5 小時*  
*難度：🔴 高*  
*優先順序：🔴 最高*
