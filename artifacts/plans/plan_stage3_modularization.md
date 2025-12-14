# Stage 3 重構規劃 - 主程式模組化

> **規劃日期**: 2024-12-14  
> **目標**: 進一步模組化 `paddle_ocr_tool.py`  
> **預計時間**: 6-8 小時  
> **狀態**: 📋 規劃中

---

## 🎯 總體目標

將 `paddle_ocr_tool.py` (2,355 行) 進一步拆分為更小、更專注的模組，提升：

- 可維護性
- 可測試性  
- 可重用性
- 代碼清晰度

---

## 📊 當前狀態分析

### 文件概況

| 項目 | 數值 |
|------|------|
| 總行數 | 2,355 行 |
| 主類別 | `PaddleOCRTool` (2,034 行) |
| 方法數 | ~50 個 |
| 已重構 | main() + 5 個巨型方法 |
| **待重構** | **核心處理邏輯** |

### 重構進度

**Stage 1 & 2 已完成**:

- ✅ CLI 邏輯提取（`paddleocr_toolkit/cli/`）
- ✅ 5 個巨型方法重構
- ✅ 輔助方法創建

**Stage 3 目標**:

- 🔄 PaddleOCRTool 核心邏輯模組化
- 🔄 OCR 處理器專業化
- 🔄 輸出處理器分離

---

## 🔍 問題分析

### 當前架構問題

#### 1. PaddleOCRTool 職責過多

**問題**: 單一類別包含 2,034 行代碼

**職責混雜**:

- OCR 引擎初始化
- 圖像處理
- PDF 處理
- 結構化分析
- 翻譯處理
- 輸出生成
- 統計收集

**影響**:

- 難以測試
- 難以維護
- 難以擴展

#### 2. 缺乏專業化處理器

**問題**: 所有處理邏輯都在主類別中

**應該分離的**:

- PDF 處理 → `PDFProcessor`
- 圖像處理 → `ImageProcessor`
- 結構化處理 → `StructureProcessor`
- 翻譯處理 → `TranslationProcessor`

#### 3. 輸出邏輯分散

**問題**: 輸出邏輯散佈在各處

**應該統一**:

- Markdown 輸出
- JSON 輸出
- Excel 輸出
- HTML 輸出

---

## 📋 重構計畫

### Phase 1: 核心邏輯提取（2-3h）

#### Task 3.1: 創建 OCR 引擎管理器

**創建**: `paddleocr_toolkit/core/ocr_engine.py`

**目標**: 管理 OCR 引擎生命週期

**預期效果**:

- PaddleOCRTool 減少 ~100 行
- 引擎管理更清晰
- 易於測試和擴展

#### Task 3.2: 創建結果解析器

**創建**: `paddleocr_toolkit/core/result_parser.py`

**目標**: 統一不同引擎的結果格式

**預期效果**:

- 結果解析邏輯集中
- 易於支援新引擎
- PaddleOCRTool 減少 ~150 行

---

### Phase 2: 處理器專業化（2-3h）

#### Task 3.3: 創建 PDF 處理器

**創建**: `paddleocr_toolkit/processors/pdf_processor.py`

**功能**:

- PDF 轉圖像
- PDF 頁面處理
- 可搜尋 PDF 生成

**預期**: PaddleOCRTool 減少 ~200 行

#### Task 3.4: 創建結構化處理器

**創建**: `paddleocr_toolkit/processors/structure_processor.py`

**功能**:

- PP-StructureV3 處理
- 排版分析
- 表格提取

**預期**: PaddleOCRTool 減少 ~250 行

#### Task 3.5: 創建翻譯處理器

**創建**: `paddleocr_toolkit/processors/translation_processor.py`

**功能**:

- 翻譯流程管理
- 雙語 PDF 生成
- 翻譯結果處理

**預期**: PaddleOCRTool 減少 ~150 行

---

### Phase 3: 輸出模組化（1-2h）

#### Task 3.6: 統一輸出管理

**創建**: `paddleocr_toolkit/outputs/output_manager.py`

**功能**:

- 統一輸出介面
- 格式化輸出
- 支援多種格式

**寫入器**:

- MarkdownWriter
- JSONWriter
- ExcelWriter
- HTMLWriter

**預期**: PaddleOCRTool 減少 ~100 行

---

### Phase 4: 主類別重組（1h）

#### Task 3.7: PaddleOCRTool 簡化

**目標**: 將 PaddleOCRTool 改為協調器

**新架構**: 組件化設計，協調各專業處理器

**預期**: 2,034 行 → ~300 行 (-85%)

---

## 📊 重構效果預估

### 代碼分布

| 模組 | 當前 | 重構後 | 變化 |
|------|------|--------|------|
| paddle_ocr_tool.py | 2,355 | 500 | -79% |
| 新增模組 | 0 | 1,855 | +1,855 |

### 新增模組明細

| 模組 | 行數 |
|------|------|
| ocr_engine.py | 200 |
| result_parser.py | 250 |
| pdf_processor.py | 400 |
| structure_processor.py | 450 |
| translation_processor.py | 300 |
| output_manager.py | 255 |

---

## 🧪 測試策略

### 新增測試

1. `test_ocr_engine.py` (10+ 測試)
2. `test_result_parser.py` (15+ 測試)
3. `test_pdf_processor.py` (20+ 測試)
4. `test_structure_processor.py` (20+ 測試)
5. `testranslation_processor.py` (15+ 測試)
6. `test_output_manager.py` (12+ 測試)

**預計新增**: 90+ 測試

**覆蓋率目標**: 84% → 88%+

---

## 📅 執行時程

### 建議分 4 天完成

**第一天** (3-4h): Task 3.1 & 3.2  
**第二天** (3-4h): Task 3.3 & 3.4  
**第三天** (2-3h): Task 3.5 & 3.6  
**第四天** (1-2h): Task 3.7 整合  

**總計**: 9-13 小時

---

## ⚠️ 風險與挑戰

### 主要風險

1. **向後兼容性** - 可能破壞現有 API
2. **引擎耦合** - PaddleOCR 不同模式行為不一
3. **複雜度** - 模組增加可能導致理解困難

### 緩解策略

- 保留舊 API 作為包裝
- 統一抽象層
- 完整文檔

---

## 🎯 成功標準

### 必須達成

- [ ] PaddleOCRTool < 500 行
- [ ] 每個處理器 < 500 行
- [ ] 所有測試通過
- [ ] 覆蓋率 > 85%
- [ ] 無功能回退

### 期望達成

- [ ] PaddleOCRTool < 400 行
- [ ] 新增 90+ 測試
- [ ] 覆蓋率 > 88%
- [ ] 文檔完整
- [ ] 性能無降低

---

## 🎉 預期成果

完成後：

1. ✅ 高度模組化 - 職責清晰
2. ✅ 易於維護 - 小模組 < 500 行
3. ✅ 易於測試 - 330+ 測試
4. ✅ 易於擴展 - 新功能簡單
5. ✅ 性能優化 - 已整合
6. ✅ 文檔完整 - 專業級

**最終評價目標**: ⭐⭐⭐⭐⭐

---

*規劃時間：2024-12-14 15:00*  
*狀態：等待審核*
