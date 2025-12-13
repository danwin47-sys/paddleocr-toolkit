# Task 2.2: 重构 `_process_hybrid_pdf()` 实作计划

> 建立时间：2024-12-14 07:05  
> 状态：📋 计划中  
> 风险等级：🟡 中等  
> 预计时间：1-1.5 小时

---

## 🎯 目标

重构 `_process_hybrid_pdf()` 方法（329 行，975-1303），将其简化为 < 150 行。

**当前状态**: 329 行  
**目标**: < 150 行（减少约 180 行，55% reduction）

---

## 📊 现状分析

### `_process_hybrid_pdf()` 方法结构（975-1303，329 行）

#### 1. **初始化阶段**（~30 行）

- 打开 PDF（1000-1004）
- 设定输出路径（1006-1007）
- 准备 PDF 生成器（1009-1027）
- 初始化变量和统计（1029-1043）

#### 2. **主处理循环**（~120 行，1045-1170）

- 页面迭代 + 进度条（1045）
- 单页处理逻辑：
  - 转换为图片（1052-1058）
  - 版面分析（1060-1103）
  - 提取 OCR 坐标（1105-1113）
  - 生成双 PDF（1115-1145）
  - 收集结果（1147-1160）
  - 内存清理（1162-1164）
- 错误处理（1166-1169）

#### 3. **输出保存阶段**（~100 行，1171-1278）

- 关闭 PDF（1171）
- 保存可搜索 PDF（1173-1176）
- 保存擦除版 PDF（1178-1181）
- 保存 Markdown（1183-1190）
- 保存 JSON（1192-1219，28 行）
- 保存 HTML（1221-1277，57 行）

#### 4. **后处理阶段**（~20 行，1279-1303）

- 翻译处理（1281-1294）
- 统计汇总（1296-1301）
- 返回结果（1303）

---

## 📋 重构策略

### 策略：提取 4 个私有方法

#### 方法 1: `_setup_hybrid_generators()` - 初始化生成器

**提取**: 1009-1027 (19 行)  
**新方法**: ~25 行

```python
def _setup_hybrid_generators(
    self,
    output_path: str
) -> Tuple[PDFGenerator, PDFGenerator, Optional[TextInpainter], str]:
    """设定混合模式所需的生成器
    
    Returns:
        Tuple of (pdf_generator, erased_generator, inpainter, erased_path)
    """
    erased_output_path = output_path.replace('_hybrid.pdf', '_erased.pdf')
    
    # 原文可搜索 PDF
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

#### 方法 2: `_process_single_hybrid_page()` - 处理单页

**提取**: 1050-1160 (110 行主循环内容)  
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
    """处理单一页面（混合模式）
    
    Returns:
        Tuple of (page_markdown, page_text, ocr_results)
    """
    # 转换为图片
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
    
    # 提取 OCR 坐标
    sorted_results = self._extract_ocr_from_structure(
        structure_output, markdown_text=page_markdown
    )
    
    # 生成双 PDF
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

#### 方法 3: `_save_hybrid_outputs()` - 保存输出文件

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
    """保存混合模式的各种输出文件"""
    
    # 保存 Markdown
    if markdown_output and all_markdown:
        self._save_markdown_output(all_markdown, markdown_output, result_summary)
    
    # 保存 JSON
    if json_output:
        self._save_json_output(all_ocr_results, json_output, pdf_path, result_summary)
    
    # 保存 HTML
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
    """从 PP-StructureV3 输出提取 Markdown
    
    Returns:
        str: 页面的 Markdown 文本
    """
    page_markdown = f"## 第 {page_num + 1} 页\n\n"
    
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
            logging.warning(f"save_to_markdown 失败: {md_err}")
            if hasattr(res, 'markdown') and isinstance(res.markdown, str):
                page_markdown += res.markdown
        finally:
            shutil.rmtree(temp_md_dir, ignore_errors=True)
    
    return page_markdown
```

---

#### 方法 5: `_generate_dual_pdfs()` - 生成双 PDF

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
    
    # 1. 原文可搜索 PDF
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
        
        # 保存到临时文件并添加
        tmp_erased_path = tempfile.mktemp(suffix='.png')
        try:
            Image.fromarray(erased_image).save(tmp_erased_path)
            erased_generator.add_page(tmp_erased_path, sorted_results)
        finally:
            if os.path.exists(tmp_erased_path):
                os.remove(tmp_erased_path)
```

---

### 额外方法（输出保存辅助）

#### 方法 6: `_save_markdown_output()` - 保存 Markdown

```python
def _save_markdown_output(
    self,
    all_markdown: List[str],
    markdown_output: str,
    result_summary: Dict[str, Any]
) -> None:
    """保存 Markdown 输出"""
    fixed_markdown = [fix_english_spacing(md) for md in all_markdown]
    with open(markdown_output, 'w', encoding='utf-8') as f:
        f.write("\n\n---\n\n".join(fixed_markdown))
    result_summary["markdown_file"] = markdown_output
    print(f"[OK] Markdown 已保存：{markdown_output}")
```

#### 方法 7: `_save_json_output()` - 保存 JSON

```python
def _save_json_output(
    self,
    all_ocr_results: List[List[OCRResult]],
    json_output: str,
    pdf_path: str,
    result_summary: Dict[str, Any]
) -> None:
    """保存 JSON 输出"""
    # JSON 序列化逻辑（28 行）
```

#### 方法 8: `_save_html_output()` - 保存 HTML

```python
def _save_html_output(
    self,
    all_markdown: List[str],
    html_output: str,
    pdf_path: str,
    result_summary: Dict[str, Any]
) -> None:
    """保存 HTML 输出"""
    # HTML 生成逻辑（57 行）
```

---

## 📊 重构后的 `_process_hybrid_pdf()`

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
    """处理 PDF 的混合模式"""
    
    # === 1. 初始化 ===
    pdf_doc = fitz.open(pdf_path)
    total_pages = len(pdf_doc)
    print(f"PDF 共 {total_pages} 页")
    
    # 设定生成器
    pdf_gen, erased_gen, inpainter, erased_path = self._setup_hybrid_generators(output_path)
    
    # 初始化收集器
    all_markdown, all_text, all_ocr_results = [], [], []
    stats = StatsCollector(pdf_path, "hybrid", total_pages)
    
    # === 2. 处理所有页面 ===
    page_iterator = range(total_pages)
    if show_progress and HAS_TQDM:
        page_iterator = tqdm(page_iterator, desc="混合模式处理中", unit="页")
    
    for page_num in page_iterator:
        try:
            stats.start_page(page_num)
            page = pdf_doc[page_num]
            
            # 处理单页
            page_md, page_txt, ocr_res = self._process_single_hybrid_page(
                page, page_num, dpi, pdf_gen, erased_gen, inpainter
            )
            
            # 收集结果
            all_markdown.append(page_md)
            all_text.append(page_txt)
            all_ocr_results.append(ocr_res)
            
            result_summary["pages_processed"] += 1
            stats.finish_page(page_num, page_txt, ocr_res)
            
        except Exception as e:
            logging.error(f"处理第 {page_num + 1} 页错误: {e}")
            continue
    
    pdf_doc.close()
    
    # === 3. 保存 PDF ===
    if pdf_gen.save():
        result_summary["searchable_pdf"] = output_path
        print(f"[OK] 可搜索 PDF 已保存：{output_path}")
    
    if erased_gen.save():
        result_summary["erased_pdf"] = erased_path
        print(f"[OK] 擦除版 PDF 已保存：{erased_path}")
    
    # === 4. 保存其他输出 ===
    self._save_hybrid_outputs(
        all_markdown, all_ocr_results,
        markdown_output, json_output, html_output,
        pdf_path, result_summary
    )
    
    result_summary["text_content"] = all_text
    
    # === 5. 翻译处理 ===
    if translate_config and HAS_TRANSLATOR and not self.debug_mode:
        self._process_translation_on_pdf(
            erased_path, all_ocr_results, translate_config,
            result_summary, dpi
        )
    
    # === 6. 完成统计 ===
    print(f"[OK] 混合模式处理完成：{result_summary['pages_processed']} 页")
    final_stats = stats.finish()
    final_stats.print_summary()
    result_summary["stats"] = final_stats.to_dict()
    
    return result_summary
```

**重构后行数**: ~80 行

---

## 📊 预期成果

### 程式码行数变化

| 项目 | 原始 | 重构后 | 减少 |
|------|------|--------|------|
| `_process_hybrid_pdf()` | 329 | **~80** | **-249** (-76%) |
| 新增方法 | 0 | **~260** | +260 |
| **净变化** | 329 | **340** | **+11** |

### 代码质量提升

- ✅ **主方法简化**: 329 → 80 行 (76% reduction)
- ✅ **职责分离**: 每个方法单一职责
- ✅ **可测试性**: 每个子方法可独立测试
- ✅ **可读性**: 清晰的步骤结构
- ✅ **可维护性**: 易于修改和扩展

---

## 📋 执行步骤

### Step 1: 提取初始化和生成器设定

- 创建 `_setup_hybrid_generators()`
- 创建 `_extract_markdown_from_structure_output()`
- 创建 `_generate_dual_pdfs()`

### Step 2: 提取单页处理逻辑

- 创建 `_process_single_hybrid_page()`

### Step 3: 提取输出保存逻辑

- 创建 `_save_markdown_output()`
- 创建 `_save_json_output()`
- 创建 `_save_html_output()`
- 创建 `_save_hybrid_outputs()`（统筹方法）

### Step 4: 简化主方法

- 重写 `_process_hybrid_pdf()` 使用新方法

### Step 5: 测试验证

- 运行现有测试
- 测试各种模式

---

## ⚠️ 注意事项

### 需要保持的功能

1. ✅ 双 PDF 生成（原文 + 擦除版）
2. ✅ 多种输出格式（MD/JSON/HTML）
3. ✅ 翻译功能整合
4. ✅ 统计收集
5. ✅ 内存管理

### 风险点

1. **内存管理**: 确保 pixmap 正确释放
2. **临时文件**: 确保清理
3. **错误处理**: 保持健壮性
4. **翻译整合**: 不破坏现有翻译功能

---

## 🎯 成功标准

- ✅ `_process_hybrid_pdf()` < 100 行
- ✅ 新增 8 个结构清晰的私有方法
- ✅ 所有测试通过
- ✅ hybrid 模式功能完全保留
- ✅ 翻译功能正常工作

---

## 💡 建议

**考虑到时间（现在 07:05）和任务复杂度**：

### 选项 A: 稍后执行（推荐）

- 这是个较大的重构（预计 1-1.5 小时）
- 已经工作了 30+ 分钟
- 可以稍后精力充沛时执行

### 选项 B: 立即执行

- 如果精力充沛可以继续
- 采用分步测试策略
- 预计 1-1.5 小时

---

*计划建立：2024-12-14 07:05*  
*预计执行时间：1-1.5 小时*  
*难度：🟡 中等*  
*优先级：🟡 中*
