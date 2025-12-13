# Task 2.3: 重构 _process_translation_on_pdf() 实作计划

> 建立时间：2024-12-14 07:26  
> 状态：📋 计划中  
> 风险等级：🔴 高  
> 预计时间：1-1.5 小时

---

## 🎯 目标

重构 `_process_translation_on_pdf()` 方法（217 行，1761-1977），将其简化为 < 100 行。

**当前状态**: 217 行  
**目标**: < 100 行（减少约 120 行，55% reduction）

---

## 📊 现状分析

### `_process_translation_on_pdf()` 方法结构（1761-1977，217 行）

#### 1. **初始化阶段**（~45 行，1785-1830）

- 提取配置参数（source_lang, target_lang等）
- 初始化 translator 和 renderer
- 打开 PDF 文档
- 创建输出路径
- 创建 PDF 生成器

#### 2. **主处理循环**（~105 行，1837-1949）

- 页面迭代 + 进度条
- 单页处理逻辑：
  - 获取 OCR 结果
  - 转换为图片
  - 翻译文字
  - 绘制翻译文字（标准模式 vs OCR workaround）
  - 添加到 PDF 生成器
- 错误处理

#### 3. **保存输出阶段**（~20 行，1951-1970）

- 关闭PDF文档
- 保存翻译版 PDF
- 保存双语版 PDF

#### 4. **错误处理**（~7 行，1971-1976）

---

## 📋 重构策略

### 策略：提取 6 个私有方法

#### 方法 1: `_setup_translation_tools()` - 初始化翻译工具

**提取**: 1806-1830 (25 行)  
**新方法**: ~35 行

```python
def _setup_translation_tools(
    self,
    erased_pdf_path: str,
    translate_config: Dict[str, Any]
) -> Tuple:
    """设定翻译所需的工具和生成器
    
    Returns:
        Tuple of (translator,  renderer, pdf_doc, hybrid_doc,
                  mono_generator, bilingual_generator, 
                  translated_path, bilingual_path)
    """
    # 初始化翻译器和绘制器
    translator = OllamaTranslator(
        model=translate_config['ollama_model'],
        base_url=translate_config['ollama_url']
    )
    renderer = TextRenderer(font_path=translate_config.get('font_path'))
    
    # 打开PDF
    pdf_doc = fitz.open(erased_pdf_path)
    
    # 打开原始hybrid PDF（用于双语）
    hybrid_pdf_path = erased_pdf_path.replace('_erased.pdf', '_hybrid.pdf')
    hybrid_doc = None
    if not translate_config['no_dual'] and os.path.exists(hybrid_pdf_path):
        hybrid_doc = fitz.open(hybrid_pdf_path)
    
    # 创建输出路径
    base_path = erased_pdf_path.replace('_erased.pdf', '')
    target_lang = translate_config['target_lang']
    translated_path = f"{base_path}_translated_{target_lang}.pdf" \
        if not translate_config['no_mono'] else None
    bilingual_path = f"{base_path}_bilingual_{target_lang}.pdf" \
        if not translate_config['no_dual'] else None
    
    # 创建生成器
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

#### 方法 2: `_get_page_images()` - 获取页面图片

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
    """获取擦除版和原始版页面图片
    
    Returns:
        Tuple of (erased_image, original_image)
    """
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    
    # 获取擦除版图片
    erased_page = pdf_doc[page_num]
    erased_pixmap = erased_page.get_pixmap(matrix=matrix)
    erased_image = pixmap_to_numpy(erased_pixmap, copy=True)
    
    # 获取原始图片（用于双语）
    original_image = erased_image.copy()
    if hybrid_doc:
        hybrid_page = hybrid_doc[page_num]
        hybrid_pixmap = hybrid_page.get_pixmap(matrix=matrix)
        original_image = pixmap_to_numpy(hybrid_pixmap, copy=True)
    
    return erased_image, original_image
```

---

#### 方法 3: `_translate_page_texts()` - 翻译页面文字

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
    """翻译页面的所有文字
    
    Returns:
        List[TranslatedBlock]: 翻译后的文字块列表
    """
    # 收集需要翻译的文字
    texts_to_translate = []
    bboxes = []
    for result in page_ocr_results:
        if result.text and result.text.strip():
            texts_to_translate.append(result.text)
            bboxes.append(result.bbox)
    
    if not texts_to_translate:
        return []
    
    logging.info(f"第 {page_num + 1} 页: 翻译 {len(texts_to_translate)} 个文字区块")
    
    # 批次翻译
    translated_texts = translator.translate_batch(
        texts_to_translate, source_lang, target_lang, show_progress=False
    )
    
    # 创建 TranslatedBlock 列表
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

#### 方法 4: `_render_translated_text()` - 绘制翻译文字

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
    """在擦除版图片上绘制翻译文字
    
    Returns:
        np.ndarray: 绘制了翻译文字的图片
    """
    if use_ocr_workaround:
        # OCR 补救模式：直接在 PDF 页面上操作
        logging.info("使用 OCR 补救模式绘制翻译文字")
        workaround = OCRWorkaround(margin=2.0, force_black=True)
        
        for block in translated_blocks:
            # 计算坐标
            x = min(p[0] for p in block.bbox)
            y = min(p[1] for p in block.bbox)
            width = max(p[0] for p in block.bbox) - x
            height = max(p[1] for p in block.bbox) - y
            
            text_block = TextBlock(
                text=block.translated_text,
                x=x, y=y, width=width, height=height
            )
            workaround.add_text_with_mask(erased_page, text_block, block.translated_text)
        
        # 从修改后的页面获取图片
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        modified_pixmap = erased_page.get_pixmap(matrix=matrix)
        translated_image = pixmap_to_numpy(modified_pixmap, copy=True)
    else:
        # 标准模式：使用 TextRenderer
        translated_image = erased_image.copy()
        translated_image = renderer.render_multiple_texts(
            translated_image, translated_blocks
        )
    
    return translated_image
```

---

#### 方法 5: `_process_single_translation_page()` - 处理单页翻译

**提取**: 1838-1944 (107 行主循环内容)  
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
    """处理单页翻译
    
    完整流程：获取图片 → 翻译 → 绘制 → 添加到生成器
    """
    # 检查 OCR 结果
    if page_num >= len(ocr_results_per_page):
        logging.warning(f"第 {page_num + 1} 页没有 OCR 结果")
        return
    
    page_ocr_results = ocr_results_per_page[page_num]
    
    # 获取页面图片
    erased_image, original_image = self._get_page_images(
        pdf_doc, hybrid_doc, page_num, dpi
    )
    
    # 如果没有 OCR 结果，直接添加空白页
    if not page_ocr_results:
        if mono_generator:
            mono_generator.add_page(erased_image)
        if bilingual_generator:
            bilingual_generator.add_bilingual_page(original_image, erased_image)
        return
    
    # 翻译文字
    translated_blocks = self._translate_page_texts(
        page_ocr_results, translator,
        translate_config['source_lang'],
        translate_config['target_lang'],
        page_num
    )
    
    # 如果没有需要翻译的文字
    if not translated_blocks:
        if mono_generator:
            mono_generator.add_page(erased_image)
        if bilingual_generator:
            bilingual_generator.add_bilingual_page(original_image, erased_image)
        return
    
    # 绘制翻译文字
    erased_page = pdf_doc[page_num] if translate_config.get('ocr_workaround') else None
    translated_image = self._render_translated_text(
        erased_image, erased_page, translated_blocks,
        renderer, translate_config.get('ocr_workaround', False), dpi
    )
    
    # 添加到生成器
    if mono_generator:
        mono_generator.add_page(translated_image)
    if bilingual_generator:
        bilingual_generator.add_bilingual_page(original_image, translated_image  )
    
    # 清理
    gc.collect()
```

---

#### 方法 6: `_save_translation_pdfs()` - 保存翻译PDF

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
    """保存翻译版和双语版 PDF"""
    # 保存翻译版 PDF
    if mono_generator and translated_path:
        if mono_generator.save(translated_path):
            result_summary["translated_pdf"] = translated_path
            print(f"[OK] 翻译 PDF 已保存：{translated_path}")
        mono_generator.close()
    
    # 保存双语版 PDF
    if bilingual_generator and bilingual_path:
        if bilingual_generator.save(bilingual_path):
            result_summary["bilingual_pdf"] = bilingual_path
            print(f"[OK] 双语对照 PDF 已保存：{bilingual_path}")
        bilingual_generator.close()
```

---

## 📊 重构后的 `_process_translation_on_pdf()`

```python
def _process_translation_on_pdf(
    self,
    erased_pdf_path: str,
    ocr_results_per_page: List[List[OCRResult]],
    translate_config: Dict[str, Any],
    result_summary: Dict[str, Any],
    dpi: int = 150
) -> None:
    """在擦除版 PDF 基础上进行翻译处理"""
    
    print(f"\n[翻译] 开始翻译处理...")
    print(f"   来源语言: {translate_config['source_lang']}")
    print(f"   目标语言: {translate_config['target_lang']}")
    print(f"   Ollama 模型: {translate_config['ollama_model']}")
    
    try:
        # === 1. 初始化工具 ===
        (translator, renderer, pdf_doc, hybrid_doc,
         mono_gen, bilingual_gen, 
         trans_path, bi_path) = self._setup_translation_tools(
            erased_pdf_path, translate_config
        )
        
        total_pages = len(pdf_doc)
        
        # === 2. 处理所有页面 ===
        page_iter = range(total_pages)
        if HAS_TQDM:
            page_iter = tqdm(page_iter, desc="翻译页面", unit="页", ncols=80)
        
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
                logging.error(f"翻译第 {page_num + 1} 页错误: {page_err}")
                logging.error(traceback.format_exc())
                continue
        
        # === 3. 保存输出 ===
        pdf_doc.close()
        if hybrid_doc:
            hybrid_doc.close()
        
        self._save_translation_pdfs(
            mono_gen, bilingual_gen,
            trans_path, bi_path,
            result_summary
        )
        
        print(f"[OK] 翻译处理完成")
        
    except Exception as e:
        error_msg = f"翻译处理失败: {str(e)}"
        logging.error(error_msg)
        logging.error(traceback.format_exc())
        print(f"错误：{error_msg}")
        result_summary["translation_error"] = str(e)
```

**重构后行数**: ~60 行

---

## 📊 预期成果

### 程式码行数变化

| 项目 | 原始 | 重构后 | 减少 |
|------|------|--------|------|
| `_process_translation_on_pdf()` | 217 | **~60** | **-157** (-72%) |
| 新增方法 | 0 | **~180** | +180 |
| **净变化** | 217 | **240** | **+23** |

### 代码质量提升

- ✅ **主方法简化**: 217 → 60 行 (72% reduction)
- ✅ **职责分离**: 每个方法单一职责
- ✅ **可测试性**: 每个子方法可独立测试
- ✅ **可读性**: 清晰的3步骤结构
- ✅ **可维护性**: 易于修改和扩展

---

## 📋 执行步骤

### Step 1: 创建 6 个辅助方法

1. `_setup_translation_tools()`
2. `_get_page_images()`
3. `_translate_page_texts()`
4. `_render_translated_text()`
5. `_process_single_translation_page()`
6. `_save_translation_pdfs()`

### Step 2: 简化主方法

- 重写 `_process_translation_on_pdf()` 使用新方法

### Step 3: 测试验证

- 运行现有测试
- 如果有翻译测试，验证功能

### Step 4: 提交 Git

---

## ⚠️ 注意事项

### 需要保持的功能

1. ✅ 双模式翻译（标准 vs OCR workaround）
2. ✅ 多种输出（单语、双语PDF）
3. ✅ 进度条显示
4. ✅ 内存管理

### 风险点

1. **翻译API调用**: 确保正确传递参数
2. **PDF操作**: PyMuPDF对象正确管理
3. **内存管理**: 及时释放pixmap
4. **错误处理**: 保持健壮性

---

## 🎯 成功标准

- ✅ `_process_translation_on_pdf()` < 100 行
- ✅ 新增 6 个结构清晰的私有方法
- ✅ 所有测试通过
- ✅ 翻译功能完全保留

---

*计划建立：2024-12-14 07:26*  
*预计执行时间：1-1.5 小时*  
*难度：🔴 高*  
*优先级：🔴 最高*
