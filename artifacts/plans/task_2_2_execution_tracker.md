## Task 2.2 執行步驟追蹤

### Step 1: 建立輔助方法（7 個新方法）

**目標**: 在 `_process_hybrid_pdf` 之前插入新方法

#### 1.1 `_setup_hybrid_generators()` ✅

- 位置: 975 行之前
- 功能: 初始化 PDF 生成器和擦除器
- 行數: ~30 行

#### 1.2 `_extract_markdown_from_structure_output()` ✅

- 功能: 從 structure 輸出提取 Markdown
- 行數: ~25 行

#### 1.3 `_generate_dual_pdfs()` ✅

- 功能: 生成原文和擦除版 PDF
- 行數: ~40 行

#### 1.4 `_process_single_hybrid_page()` ✅

- 功能: 處理單頁的核心邏輯
- 行數: ~65 行

#### 1.5 `_save_markdown_output()` ✅

- 功能: 儲存 Markdown 檔案
- 行數: ~10 行

#### 1.6 `_save_json_output()` ✅  

- 功能: 儲存 JSON 檔案
- 行數: ~30 行

#### 1.7 `_save_html_output()` ✅

- 功能: 儲存 HTML 檔案
- 行數: ~60 行

#### 1.8 `_save_hybrid_outputs()` ✅

- 功能: 統籌儲存所有輸出
- 行數: ~15 行

---

### Step 2: 簡化主方法 `_process_hybrid_pdf()`

- 原始: 329 行
- 目標: < 100 行
- 使用新建立的輔助方法

---

### Step 3: 測試驗證

- 執行完整測試套件
- 測試 hybrid 模式功能

---

### Step 4: 提交 Git

- 提交重構成果
