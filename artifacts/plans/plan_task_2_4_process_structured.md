# Task 2.4: 重構 process_structured() - 快速實用方案

> 建立時間：2024-12-14 07:44  
> 狀態：📋 規劃中  
> 風險等級：🟡 中等  
> 預計時間：30-40 分鐘（快速方案）

---

## 🎯 目標

重構 `process_structured()` 方法（167 行），採用**快速實用方案**簡化到 < 100 行。

**當前狀態**: 167 行（429-594）  
**目標**: < 100 行（減少約 70 行，40% reduction）

---

## 📊 現狀分析

### `process_structured()` 方法結構（167 行）

#### 主要邏輯塊

1. **初始化**（~10 行）- 驗證模式、建立 result_summary
2. **路徑處理**（~20 行）- 處理 markdown/json 輸出路徑
3. **主迴圈**（~120 行）- 處理每個頁面的輸出
   - Markdown 輸出（~15 行）
   - JSON 輸出（~15 行）
   - Excel 輸出（~25 行）
   - HTML 輸出（~45 行）
4. **最終儲存**（~15 行）- 合併 markdown，儲存 HTML

---

## 📋 快速重構策略（實用方案）

考慮到時間限制，採用**聚焦關鍵重複邏輯**的策略：

### 核心問題識別

重複模式最明顯的是：

1. **臨時目錄建立和清理** - 重複 4 次
2. **路徑處理邏輯** - markdown/json 重複
3. **檔案儲存模板** - 類似邏輯重複

### 提取 3 個關鍵方法

#### 方法 1: `_process_output_with_tempdir()` - 通用臨時目錄處理

**作用**: 消除臨時目錄的重複邏輯  
**預計**: ~20 行

```python
def _process_output_with_tempdir(
    self,
    res,  # Structure result object
    save_method_name: str,  # 'save_to_markdown', 'save_to_json', etc.
    glob_pattern: str,  # '*.md', '*.json', etc.
    process_file: Callable  # 處理檔案的回撥函式
) -> None:
    """使用臨時目錄處理輸出的通用方法"""
    temp_dir = tempfile.mkdtemp()
    try:
        # 呼叫儲存方法
        save_method = getattr(res, save_method_name, None)
        if save_method:
            save_method(save_path=temp_dir)
            # 處理生成的檔案
            for file in Path(temp_dir).glob(glob_pattern):
                process_file(file)
    except Exception as e:
        logging.warning(f"{save_method_name} 失敗: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
```

#### 方法 2: `_save_structured_markdown()` - Markdown 儲存

**作用**: 提取 markdown 合併邏輯  
**預計**: ~15 行

```python
def _save_structured_markdown(
    self,
    all_markdown_content: List[str],
    markdown_output: str,
    result_summary: Dict[str, Any]
) -> None:
    """儲存合併後的 Markdown"""
    if all_markdown_content:
        combined = "\n\n---\n\n".join(all_markdown_content)
        with open(markdown_output, 'w', encoding='utf-8') as f:
            f.write(combined)
        result_summary["markdown_files"].append(markdown_output)
        print(f"[OK] Markdown 已儲存：{markdown_output}")
```

#### 方法 3: `_save_structured_html()` - HTML 儲存

**作用**: 提取 HTML 生成邏輯  
**預計**: ~50 行（HTML 生成程式碼很長）

---

## 📊 預期成果（快速方案）

### 程式碼行數變化

| 專案 | 原始 | 重構後 | 減少 |
|------|------|--------|------|
| `process_structured()` | 167 | **~95** | **-72** (-43%) |
| 新增方法 | 0 | **~85** | +85 |
| **淨變化** | 167 | **180** | **+13** |

### 程式碼質量提升

- ✅ **主方法簡化**: 167 → 95 行 (43% reduction)
- ✅ **消除重複**: 臨時目錄處理統一
- ✅ **可讀性**: 更清晰的結構
- ✅ **可維護性**: 易於修改輸出邏輯

---

## 🎯 執行計劃（30-40 分鐘）

### 快速實施（考慮時間限制）

**Step 1**: 建立 3 個輔助方法（15 分鐘）  
**Step 2**: 簡化主方法（10 分鐘）  
**Step 3**: 測試驗證（5-10 分鐘）  
**Step 4**: 提交 Git（5 分鐘）

---

## ⚠️ 務實建議

考慮到：

- 你已工作 1.5 小時
- 已完成 3 個重大任務
- 這是第 4 個重構任務

**建議採用快速方案**：

- 只提取最關鍵的重複邏輯
- 目標 < 100 行即可（不追求極致）
- 保持程式碼清晰可讀

---

## 🎯 成功標準

- ✅ `process_structured()` < 100 行
- ✅ 新增 2-3 個清晰的輔助方法
- ✅ 所有測試透過
- ✅ 功能完全保留

---

*計劃建立：2024-12-14 07:44*  
*預計執行時間：30-40 分鐘*  
*難度：🟡 中等*  
*方案：快速實用型*
