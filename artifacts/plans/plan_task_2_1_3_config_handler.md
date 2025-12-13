# Task 2.1.3: 提取設定檔處理實作計畫

> 建立時間：2024-12-13 23:59  
> 完成時間：2024-12-14 00:03  
> 狀態：✅ **已完成**  
> 風險等級：🟢 低

---

## 🎯 目標

將 `main()` 函數中的參數處理邏輯（約 18 行，1960-1977）提取到 `config_handler.py`。

---

## 📊 現狀分析

### `main()` 中需要提取的邏輯（第 1960-1977 行）

1. **`--no-*` 選項處理**（9 行）
   - `--no-searchable`
   - `--no-text-output`
   - `--no-markdown-output`
   - `--no-json-output`

2. **`--all` 參數處理**（7 行）
   - 在 structure/vl/hybrid 模式啟用所有輸出格式

---

## 📋 執行步驟

### Step 1: 增強 `config_handler.py`

**新增方法**：

#### 1.1 `process_args_overrides()` - 處理參數覆蓋

```python
import argparse

def process_args_overrides(args: argparse.Namespace) -> argparse.Namespace:
    """處理 CLI 參數的覆蓋邏輯
    
    包含：
    1. 處理 --no-* 選項覆蓋
    2. 處理 --all 參數啟用所有輸出
    
    Args:
        args: 命令列參數
    
    Returns:
        argparse.Namespace: 處理後的參數
    """
    # 處理 --no-* 選項來覆蓋預設值
    args = _process_no_flags(args)
    
    # 處理 --all 參數：一次啟用所有輸出格式
    args = _process_all_flag(args)
    
    return args

def _process_no_flags(args: argparse.Namespace) -> argparse.Namespace:
    """處理 --no-* 覆蓋選項"""
    if args.no_searchable:
        args.searchable = False
    if args.no_text_output:
        args.text_output = None
    if args.no_markdown_output:
        args.markdown_output = None
    if args.no_json_output:
        args.json_output = None
    
    return args

def _process_all_flag(args: argparse.Namespace) -> argparse.Namespace:
    """處理 --all 參數"""
    if hasattr(args, 'all') and args.all:
        if args.mode in ['structure', 'vl', 'hybrid']:
            args.markdown_output = args.markdown_output or 'AUTO'
            args.json_output = args.json_output or 'AUTO'
            args.html_output = args.html_output or 'AUTO'
            print(f"[--all] 啟用所有輸出格式：Markdown, JSON, HTML")
    
    return args
```

---

### Step 2: 在 `main()` 中使用新方法

**修改位置**：`paddle_ocr_tool.py` 第 1960-1977 行

**原始程式碼**（18 行）：

```python
# 處理 --no-* 選項來覆蓋預設值
if args.no_searchable:
    args.searchable = False
if args.no_text_output:
    args.text_output = None
if args.no_markdown_output:
    args.markdown_output = None
if args.no_json_output:
    args.json_output = None

# 處理 --all 參數：一次啟用所有輸出格式
if hasattr(args, 'all') and args.all:
    if args.mode in ['structure', 'vl', 'hybrid']:
        args.markdown_output = args.markdown_output or 'AUTO'
        args.json_output = args.json_output or 'AUTO'
        args.html_output = args.html_output or 'AUTO'
        print(f"[--all] 啟用所有輸出格式：Markdown, JSON, HTML")
```

**新程式碼**（3 行）：

```python
# 處理參數覆蓋（--no-* 和 --all）
from paddleocr_toolkit.cli import process_args_overrides
args = process_args_overrides(args)
```

**預期減少**：main() 從 ~276 行 → **~261 行** (-15 行)

---

### Step 3: 更新 `cli/__init__.py`

確保新函數被正確匯出：

```python
from .config_handler import (
    load_and_merge_config,
    load_config_file,
    process_args_overrides  # 新增
)

__all__ = [
    'create_argument_parser',
    'OutputPathManager',
    'load_and_merge_config',
    'load_config_file',
    'process_args_overrides',  # 新增
]
```

---

### Step 4: 測試驗證

#### 測試 1: 基本功能測試

```bash
# 測試 --no-* 選項
python paddle_ocr_tool.py test.pdf --no-searchable
python paddle_ocr_tool.py test.pdf --mode hybrid --no-markdown-output

# 測試 --all 參數
python paddle_ocr_tool.py test.pdf --mode hybrid --all
```

#### 測試 2: 執行測試套件

```bash
pytest tests/ -v
```

---

## 📊 預期成果

### 程式碼行數變化

| 檔案 | 變化 | 說明 |
|------|------|------|
| `paddle_ocr_tool.py` | **-15 行** | 移除參數處理邏輯 |
| `cli/config_handler.py` | **+45 行** | 新增處理方法 |
| `cli/__init__.py` | **+2 行** | 匯出新函數 |
| **淨變化** | **+32 行** | 模組化開銷 |

### `main()` 函數簡化

- **當前**: ~276 行
- **目標**: ~261 行
- **減少**: **~15 行** (5.4% 減少)

### Task 2.1 整體進度

- Step 1 完成: -300 行
- Step 2 完成: -59 行
- Step 3 完成: -15 行
- **累計減少**: **-374 行** (635 → 261, 58.9% 完成)

---

## ⚠️ 注意事項

### 需要處理的細節

1. ✅ 保持參數處理順序
2. ✅ `--all` 參數的 print 訊息保留
3. ✅ 正確處理 `hasattr()` 檢查
4. ✅ 確保所有 `--no-*` 選項都被處理

### 測試重點

1. `--no-*` 選項正確覆蓋預設值
2. `--all` 參數只在支援的模式啟用
3. 參數處理順序不影響結果

---

## 🎯 成功標準

- ✅ `config_handler.py` 新增處理方法
- ✅ `main()` 減少 ~15 行
- ✅ `--no-*` 和 `--all` 功能正常
- ✅ 測試全部通過
- ✅ CLI 功能無破壞性變更

---

*計畫建立：2024-12-13 23:59*  
*預計執行時間：10-15 分鐘*  
*下一步：開始實作 Step 1*
