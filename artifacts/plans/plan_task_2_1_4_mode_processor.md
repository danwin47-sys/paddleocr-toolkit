# Task 2.1.4: 提取模式分發邏輯實作計劃

> 建立時間：2024-12-14 06:50  
> 狀態：⏳ 執行中  
> 風險等級：🔴 高（最大的重構任務）

---

## 🎯 目標

將 `main()` 函式中的模式處理邏輯（約 187 行，2015-2201）提取到獨立的模式處理器。

---

## 📊 現狀分析

### `main()` 中的模式處理邏輯（第 2015-2201 行）

**總計：187 行**

#### 1. **formula 模式**（13 行，2015-2027）

```python
if args.mode == "formula":
    result = tool.process_formula(...)
    # 結果顯示
```

#### 2. **structure/vl 模式**（22 行，2029-2050）

```python
elif args.mode in ["structure", "vl"]:
    result = tool.process_structured(...)
    # 結果顯示
```

#### 3. **hybrid 模式**（74 行，2052-2125）

- hybrid + translation（54 行）
- hybrid 普通模式（20 行）

#### 4. **basic 模式**（74 行，2127-2201）

- 目錄處理
- PDF 處理
- 圖片處理
- 文字輸出

---

## 📋 執行策略

### 策略選擇：建立 ModeProcessor 類

不建立複雜的 ModeDispatcher，而是建立一個簡單的 `ModeProcessor` 類來封裝模式處理邏輯。

#### 新檔案：`paddleocr_toolkit/cli/mode_processor.py`

```python
class ModeProcessor:
    """處理不同 OCR 模式的執行和結果顯示"""
    
    def __init__(self, tool, args, input_path):
        self.tool = tool
        self.args = args
        self.input_path = input_path
    
    def process(self) -> Dict[str, Any]:
        """根據模式執行處理"""
        if self.args.mode == "formula":
            return self._process_formula()
        elif self.args.mode in ["structure", "vl"]:
            return self._process_structured()
        elif self.args.mode == "hybrid":
            return self._process_hybrid()
        else:  # basic
            return self._process_basic()
    
    def _process_formula(self):
        """處理 formula 模式"""
        # 提取 formula 邏輯
    
    def _process_structured(self):
        """處理 structure/vl 模式"""
        # 提取 structure/vl 邏輯
    
    def _process_hybrid(self):
        """處理 hybrid 模式"""
        # 提取 hybrid 邏輯（包括翻譯）
    
    def _process_basic(self):
        """處理 basic 模式"""
        # 提取 basic 邏輯
```

---

## 📋 執行步驟

### Step 1: 建立 `mode_processor.py`

**建立檔案**: `paddleocr_toolkit/cli/mode_processor.py`

**包含**:

- `ModeProcessor` 類
- 4 個模式處理方法
- 結果顯示輔助方法

**預計行數**: ~250 行

---

### Step 2: 在 `main()` 中使用 `ModeProcessor`

**原始程式碼**（187 行）:

```python
# 根據模式處理
if args.mode == "formula":
    # 公式識別模式
    result = tool.process_formula(...)
    if result.get("error"):
        print(...)
    else:
        print(...)
elif args.mode in ["structure", "vl"]:
    # 結構化處理模式
    ...
elif args.mode == "hybrid":
    # 混合模式
    ...
else:
    # basic 模式
    ...
```

**新程式碼**（~10 行）:

```python
# 使用模式處理器執行 OCR
from paddleocr_toolkit.cli import ModeProcessor
processor = ModeProcessor(tool, args, input_path)
result = processor.process()

# 模式處理器已包含結果顯示
# 無需額外處理
```

**預期減少**: main() 從 ~262 行 → **~85 行** (-177 行)

---

### Step 3: 更新 `cli/__init__.py`

```python
from .mode_processor import ModeProcessor

__all__ = [
    'create_argument_parser',
    'OutputPathManager',
    'load_and_merge_config',
    'load_config_file',
    'process_args_overrides',
    'ModeProcessor',  # 新增
]
```

---

### Step 4: 測試驗證

#### 測試 1: 各種模式功能測試

```bash
# 測試 formula 模式
python paddle_ocr_tool.py test.png --mode formula

# 測試 structure 模式
python paddle_ocr_tool.py test.pdf --mode structure

# 測試 hybrid 模式
python paddle_ocr_tool.py test.pdf --mode hybrid

# 測試 basic 模式
python paddle_ocr_tool.py test.pdf
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
| `paddle_ocr_tool.py` | **-177 行** | 移除模式處理邏輯 |
| `cli/mode_processor.py` | **+250 行** | 新增模式處理器 |
| `cli/__init__.py` | **+2 行** | 匯出新類 |
| **淨變化** | **+75 行** | 模組化開銷 |

### `main()` 函式簡化

- **當前**: ~262 行
- **目標**: ~85 行
- **減少**: **~177 行** (67.6% 減少)

### Task 2.1 整體進度

- Step 1 完成: -300 行
- Step 2 完成: -59 行
- Step 3 完成: -14 行
- Step 4 完成: -177 行
- **累計減少**: **-550 行** (635 → 85, **86.6% 完成**)

---

## ⚠️ 注意事項

### 需要處理的細節

1. ✅ 保持所有模式的功能完整
2. ✅ 結果顯示邏輯一致
3. ✅ 錯誤處理不變
4. ✅ `show_progress` 引數正確傳遞
5. ✅ 翻譯功能完整保留
6. ✅ `SUPPORTED_IMAGE_FORMATS` 和 `SUPPORTED_PDF_FORMAT` 常量訪問

### 可能的挑戰

1. **basic 模式複雜**: 需要處理目錄/PDF/圖片三種輸入
2. **hybrid + translation**: 翻譯邏輯較複雜
3. **結果顯示多樣**: 每個模式的輸出格式不同
4. **全域性常量**: 需要正確引用 `SUPPORTED_*` 常量

---

## 🎯 成功標準

- ✅ `ModeProcessor` 類功能完整
- ✅ `main()` 減少 ~177 行
- ✅ 所有模式功能正常
- ✅ 測試全部透過
- ✅ CLI 功能無破壞性變更

---

## 💡 實作建議

### 分步實作（降低風險）

**階段 1**: 先提取簡單模式

- formula (13 行)
- structure/vl (22 行)

**階段 2**: 提取 hybrid 模式

- hybrid 普通 (20 行)
- hybrid + translation (54 行)

**階段 3**: 提取 basic 模式（最複雜）

- basic 全部邏輯 (74 行)

**階段 4**: 測試和驗證

---

*計劃建立：2024-12-14 06:50*  
*預計執行時間：1-1.5 小時*  
*下一步：開始實作 Step 1*
