# Task 2.1.2: 提取輸出路徑管理實作計畫

> 建立時間：2024-12-13 23:55  
> 完成時間：2024-12-14 00:00  
> 狀態：✅ **已完成**  
> 風險等級：🟡 中等

---

## 🎯 目標

將 `main()` 函數中的輸出路徑處理邏輯（約 70 行，1978-2046）提取並完善 `OutputPathManager` 類。

---

## 📊 現狀分析

### 已有實現 (`output_manager.py`)

✅ **已實現的方法**：

- `get_searchable_pdf_path()`
- `get_text_output_path()`
- `get_markdown_output_path()`
- `get_json_output_path()`
- `get_html_output_path()`
- `get_excel_output_path()`
- `get_latex_output_path()`

### `main()` 中的路徑處理邏輯（第 1978-2046 行）

**需要提取的功能**：

1. **模式特定的輸出路徑處理**（47 行）
   - basic 模式路徑
   - formula 模式路徑
   - hybrid 模式路徑
   - structure/vl 模式路徑

2. **輸出設定摘要顯示**（20 行）
   - 根據模式顯示不同的輸出資訊

---

## 📋 執行步驟

### Step 1: 增強 `OutputPathManager` 類

**新增方法**：

#### 1.1 `process_mode_outputs()` - 根據模式處理所有輸出路徑

```python
def process_mode_outputs(
    self,
    args: argparse.Namespace,
    script_dir: Path
) -> argparse.Namespace:
    """根據 OCR 模式處理所有輸出路徑設定
    
    Args:
        args: 命令列參數
        script_dir: 腳本所在目錄
    
    Returns:
        argparse.Namespace: 更新後的參數
    """
    # 根據模式設定預設輸出路徑
    if self.mode == "basic":
        args = self._process_basic_mode_outputs(args, script_dir)
    elif self.mode == "formula":
        args = self._process_formula_mode_outputs(args, script_dir)
    elif self.mode == "hybrid":
        args = self._process_hybrid_mode_outputs(args, script_dir)
    else:  # structure/vl
        args = self._process_structure_mode_outputs(args, script_dir)
    
    return args
```

#### 1.2 私有方法：各模式的輸出處理

```python
def _process_basic_mode_outputs(
    self, 
    args: argparse.Namespace, 
    script_dir: Path
) -> argparse.Namespace:
    """處理 basic 模式的輸出設定"""
    if args.text_output == 'AUTO':
        args.text_output = str(script_dir / f"{self.base_name}_ocr.txt")
    
    # 忽略其他模式專用的輸出
    args.markdown_output = None
    args.json_output = None
    args.excel_output = None
    args.latex_output = None
    
    return args

def _process_formula_mode_outputs(...):
    """處理 formula 模式的輸出設定"""
    # 類似實現

def _process_hybrid_mode_outputs(...):
    """處理 hybrid 模式的輸出設定"""
    # 類似實現

def _process_structure_mode_outputs(...):
    """處理 structure/vl 模式的輸出設定"""
    # 類似實現
```

#### 1.3 `print_output_summary()` - 顯示輸出設定摘要

```python
def print_output_summary(self, args: argparse.Namespace) -> None:
    """顯示輸出設定摘要
    
    Args:
        args: 命令列參數
    """
    print(f"\n[輸入] {self.input_path}")
    print(f"[模式] {self.mode}")
    
    if self.mode == "basic":
        self._print_basic_mode_summary(args)
    elif self.mode == "formula":
        self._print_formula_mode_summary(args)
    elif self.mode == "hybrid":
        self._print_hybrid_mode_summary(args)
    else:
        self._print_structure_mode_summary(args)
    
    print()
```

---

### Step 2: 在 `main()` 中使用 `OutputPathManager`

**修改位置**：`paddle_ocr_tool.py` 第 1978-2046 行

**原始程式碼**（約 70 行）：

```python
# 根據模式設定預設輸出路徑
if args.mode == "basic":
    if args.text_output == 'AUTO':
        args.text_output = str(script_dir / f"{base_name}_ocr.txt")
    # ... 47 行
# 顯示輸出設定摘要
print(f"\n[輸入] {input_path}")
# ... 20 行
```

**新程式碼**（約 10 行）：

```python
# 使用 OutputPathManager 處理輸出路徑
output_manager = OutputPathManager(str(input_path), args.mode)
args = output_manager.process_mode_outputs(args, script_dir)

# 顯示輸出設定摘要
output_manager.print_output_summary(args)

# 顯示進度條設定
if not args.no_progress and HAS_TQDM:
    print(f"[進度條] 啟用")
```

**預期減少**：main() 從 ~335 行 → **~275 行** (-60 行)

---

### Step 3: 測試驗證

#### 測試 1: 基本功能測試

```bash
# 測試各種模式的輸出路徑
python paddle_ocr_tool.py test.pdf --mode basic
python paddle_ocr_tool.py test.pdf --mode structure
python paddle_ocr_tool.py test.pdf --mode hybrid
python paddle_ocr_tool.py test.pdf --mode formula
```

#### 測試 2: 自訂輸出路徑

```bash
python paddle_ocr_tool.py test.pdf --text-output custom.txt
python paddle_ocr_tool.py test.pdf --mode hybrid --markdown-output custom.md
```

#### 測試 3: 執行測試套件

```bash
pytest tests/ -v
```

---

### Step 4: 提交變更

**Git 提交訊息**：

```
refactor(cli): Extract output path management (Task 2.1.2)

- Enhance OutputPathManager with process_mode_outputs()
- Add print_output_summary() for consistent output display
- Reduce main() function by ~60 lines
- All tests passing

Part of Stage 2 refactoring plan (Task 2.1)
```

---

## 📊 預期成果

### 程式碼行數變化

| 檔案 | 變化 | 說明 |
|------|------|------|
| `paddle_ocr_tool.py` | **-60 行** | 移除輸出路徑處理邏輯 |
| `cli/output_manager.py` | **+60 行** | 新增處理方法 |
| **淨變化** | **0 行** | 程式碼重組，無額外開銷 |

### `main()` 函數簡化

- **當前**: ~335 行
- **目標**: ~275 行
- **減少**: **~60 行** (18% 減少)

### Task 2.1 整體進度

- Step 1 完成: -300 行
- Step 2 完成: -60 行
- **累計減少**: **-360 行** (635 → 275, 57% 完成)

---

## ⚠️ 注意事項

### 需要處理的邊界情況

1. ✅ `script_dir` vs `parent_dir` 路徑差異
2. ✅ `AUTO` 關鍵字處理
3. ✅ 模式切換時清空不相關的輸出
4. ✅ 進度條設定（保留在 main）

### 測試重點

1. 所有模式的預設路徑生成
2. 自訂路徑覆蓋
3. `--all` 參數的行為
4. 輸出摘要格式正確

---

## 🎯 成功標準

- ✅ `OutputPathManager` 功能完整
- ✅ `main()` 減少 ~60 行
- ✅ 所有模式的輸出路徑正確
- ✅ 測試全部通過
- ✅ CLI 功能無破壞性變更

---

*計畫建立：2024-12-13 23:55*  
*預計執行時間：30-40 分鐘*  
*下一步：開始實作 Step 1*
