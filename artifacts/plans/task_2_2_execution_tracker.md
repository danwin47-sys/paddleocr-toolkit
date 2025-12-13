## Task 2.2 执行步骤追踪

### Step 1: 创建辅助方法（7 个新方法）

**目标**: 在 `_process_hybrid_pdf` 之前插入新方法

#### 1.1 `_setup_hybrid_generators()` ✅

- 位置: 975 行之前
- 功能: 初始化 PDF 生成器和擦除器
- 行数: ~30 行

#### 1.2 `_extract_markdown_from_structure_output()` ✅

- 功能: 从 structure 输出提取 Markdown
- 行数: ~25 行

#### 1.3 `_generate_dual_pdfs()` ✅

- 功能: 生成原文和擦除版 PDF
- 行数: ~40 行

#### 1.4 `_process_single_hybrid_page()` ✅

- 功能: 处理单页的核心逻辑
- 行数: ~65 行

#### 1.5 `_save_markdown_output()` ✅

- 功能: 保存 Markdown 文件
- 行数: ~10 行

#### 1.6 `_save_json_output()` ✅  

- 功能: 保存 JSON 文件
- 行数: ~30 行

#### 1.7 `_save_html_output()` ✅

- 功能: 保存 HTML 文件
- 行数: ~60 行

#### 1.8 `_save_hybrid_outputs()` ✅

- 功能: 统筹保存所有输出
- 行数: ~15 行

---

### Step 2: 简化主方法 `_process_hybrid_pdf()`

- 原始: 329 行
- 目标: < 100 行
- 使用新创建的辅助方法

---

### Step 3: 测试验证

- 运行完整测试套件
- 测试 hybrid 模式功能

---

### Step 4: 提交 Git

- 提交重构成果
