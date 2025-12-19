# 程式碼重構計畫：依照 Antigravity 架構

> 建立時間：2024-12-13 22:42  
> 狀態：⏳ 規劃中

---

## 📋 重構目標

### 主要目標

1. **提升測試覆蓋率**：從 76% → 80%+
2. **改善程式碼品質**：遵循 `.agent/rules.md` 的編碼標準
3. **降低技術債**：分階段重構 `paddle_ocr_tool.py`（2600 行）
4. **增強可維護性**：增加檔案字串、型別提示

### 非目標

- ❌ 不改變現有功能
- ❌ 不破壞現有 API
- ❌ 不降低測試覆蓋率

---

## 🎯 重構策略：分階段進行

### 階段 1：低風險改善（1-2 天）

**目標**：提升測試覆蓋率，不修改主要邏輯

- [ ] 為低覆蓋模組新增測試
- [ ] 增加型別提示和 docstrings
- [ ] 修復 lint 錯誤

### 階段 2：中風險重構（3-5 天）

**目標**：整理模組內部結構

- [ ] 拆分過長函式（> 100 行）
- [ ] 提取重複邏輯
- [ ] 最佳化錯誤處理

### 階段 3：高風險重構（1-2 週）

**目標**：重構主程式

- [ ] 拆分 `paddle_ocr_tool.py`
- [ ] 建立新模組
- [ ] 遷移功能

---

## 📊 當前狀態分析

### 模組覆蓋率（由低到高）

| 模組 | 覆蓋率 | 優先順序 | 狀態 |
|------|--------|--------|------|
| `image_preprocessor.py` | 66% | 🔴 高 | 待改善 |
| `pdf_generator.py` | 69% | 🔴 高 | 待改善 |
| `pdf_utils.py` | 70% | 🟡 中 | 待改善 |
| `pdf_quality.py` | 70% | 🟡 中 | 待改善 |
| `ocr_workaround.py` | 76% | 🟢 低 | 可接受 |
| `stats_collector.py` | 80% | ✅ | 良好 |
| `config_loader.py` | 80% | ✅ | 良好 |
| `batch_processor.py` | 82% | ✅ | 良好 |
| `glossary_manager.py` | 83% | ✅ | 良好 |
| `text_processor.py` | 90% | ✅ | 優秀 |
| `models.py` | 100% | ✅ | 完美 |

### 程式碼品質問題

1. **主程式過大**
   - `paddle_ocr_tool.py`: 2,600 行
   - 包含過多邏輯
   - 難以測試和維護

2. **缺少型別提示**
   - 部分舊程式碼沒有型別提示
   - 影響 IDE 支援和可讀性

3. **檔案字串不完整**
   - 部分函式缺少 docstrings
   - 部分 docstrings 不符合 Google Style

---

## 🗓️ 階段 1：低風險改善（執行中）

### Task 1.1: 提升 `image_preprocessor.py` 覆蓋率

**當前**：66%  
**目標**：75%+  
**預估工時**：2 小時

#### 分析

```bash
pytest tests/test_image_preprocessor.py --cov=paddleocr_toolkit.processors.image_preprocessor --cov-report=term-missing
```

**缺失測試**：

- [ ] `deskew_image()` 的邊界條件
- [ ] `auto_preprocess()` 的不同模式
- [ ] 錯誤處理測試

#### 行動計畫

1. 檢視當前測試
2. 識別未覆蓋的程式碼路徑
3. 撰寫新測試
4. 執行並驗證

**實作計畫**：`artifacts/plans/plan_improve_image_preprocessor_coverage.md`

---

### Task 1.2: 提升 `pdf_generator.py` 覆蓋率

**當前**：69%  
**目標**：75%+  
**預估工時**：3 小時

#### 分析

主要未覆蓋部分：

- `_insert_invisible_text()` 的字型選擇邏輯
- 壓縮模式的不同路徑
- 錯誤處理分支

#### 行動計畫

1. 分析未覆蓋的程式碼行
2. 設計測試案例
3. 實作測試
4. 驗證覆蓋率提升

**實作計畫**：`artifacts/plans/plan_improve_pdf_generator_coverage.md`

---

### Task 1.3: 為現有程式碼新增型別提示

**範圍**：所有缺少型別提示的公開 API  
**預估工時**：2 小時

#### 檢查清單

- [ ] `core/` 模組
- [ ] `processors/` 模組
- [ ] 主程式中的關鍵函式

#### 範例

```python
# 前
def process_data(data):
    return data.upper()

# 後
def process_data(data: str) -> str:
    """處理資料。
    
    Args:
        data: 輸入資料。
        
    Returns:
        處理後的資料。
    """
    return data.upper()
```

---

### Task 1.4: 補充缺少的 Docstrings

**範圍**：所有公開函式和類別  
**預估工時**：2 小時

#### Google Style Docstrings 模板

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """簡短描述（一行）。
    
    詳細描述（可選，多行）。
    
    Args:
        param1: 引數 1 的說明。
        param2: 引數 2 的說明。
        
    Returns:
        返回值的說明。
        
    Raises:
        ErrorType: 錯誤情況的說明。
    """
    pass
```

---

## 🗓️ 階段 2：中風險重構（待執行）

### Task 2.1: 重構過長函式

**識別標準**：> 100 行的函式  
**預估工時**：4-6 小時

#### 候選函式

1. `paddle_ocr_tool.py` 中的主處理函式
2. `pdf_generator.py` 的某些方法

#### 重構策略

- 提取子函式
- 使用輔助類別
- 簡化邏輯

---

### Task 2.2: 提取重複邏輯

**範圍**：整個專案  
**預估工時**：3-4 小時

#### 重複模式

1. 檔案路徑處理
2. 錯誤訊息格式化
3. 進度回撥

---

### Task 2.3: 改善錯誤處理

**目標**：統一的錯誤處理策略  
**預估工時**：2-3 小時

#### 改善方向

- 使用自訂異常類別
- 提供有意義的錯誤訊息
- 適當的日誌記錄

---

## 🗓️ 階段 3：高風險重構（待規劃）

### Task 3.1: 拆分 `paddle_ocr_tool.py`

**當前**：2,600 行單一檔案  
**目標**：< 500 行主程式 + 多個模組  
**預估工時**：5-7 天

#### 拆分策略（待詳細規劃）

```
paddle_ocr_tool.py (500 行)
├── cli/
│   ├── argument_parser.py     # CLI 引數解析
│   └── output_manager.py      # 輸出管理
├── engine/
│   ├── ocr_engine.py          # OCR 引擎封裝
│   └── mode_handlers.py       # 不同模式的處理器
└── pipeline/
    ├── preprocessing.py       # 前處理管線
    └── postprocessing.py      # 後處理管線
```

#### 風險

- ⚠️ 可能破壞現有功能
- ⚠️ 需要大量測試
- ⚠️ 需要謹慎的逐步遷移

---

## 📝 執行原則

### 1. Artifact-First

每個重構任務都要先建立計畫：

```
artifacts/plans/plan_[task_name].md
```

### 2. 測試驅動

- 重構前：確保現有測試透過
- 重構中：保持測試綠燈
- 重構後：增加新測試

### 3. 小步前進

每次提交應該：

- 功能完整
- 測試透過
- 可獨立審查

### 4. 檔案同步

重構後立即更新：

- Docstrings
- README.md（如果影響使用）
- `.agent/context/architecture.md`（如果影響架構）

---

## ✅ 檢查清單（每個任務）

### 開始前

- [ ] 建立實作計畫（`artifacts/plans/`）
- [ ] 確認當前測試全部透過
- [ ] 記錄當前覆蓋率

### 執行中

- [ ] 遵循 `.agent/rules.md`
- [ ] 保持測試綠燈
- [ ] 及時提交小變更

### 完成後

- [ ] 所有測試透過
- [ ] 覆蓋率不降低（最好提升）
- [ ] 更新相關檔案
- [ ] Code review（自我審查）
- [ ] 提交並推送

---

## 📊 進度追蹤

### 階段 1 進度：0/4 (0%)

- [ ] Task 1.1: `image_preprocessor` 覆蓋率 (66% → 75%)
- [ ] Task 1.2: `pdf_generator` 覆蓋率 (69% → 75%)
- [ ] Task 1.3: 新增型別提示
- [ ] Task 1.4: 補充 docstrings

### 階段 2 進度：未開始

- [ ] Task 2.1: 重構過長函式
- [ ] Task 2.2: 提取重複邏輯
- [ ] Task 2.3: 改善錯誤處理

### 階段 3 進度：未開始

- [ ] Task 3.1: 拆分主程式（需詳細規劃）

---

## 📅 時間規劃

### 本週（Week 1）

- 完成階段 1（Task 1.1 - 1.4）
- 目標：覆蓋率 76% → 78%+

### 下週（Week 2）

- 開始階段 2（Task 2.1 - 2.3）
- 目標：覆蓋率 78% → 80%+

### 未來（Month 1-2）

- 規劃並執行階段 3
- 目標：主程式重構完成

---

## 🎯 成功指標

### 量化指標

- ✅ 測試覆蓋率：76% → **80%+**
- ✅ 主程式行數：2,600 → **< 1,000**
- ✅ 平均函式長度：**< 50 行**
- ✅ 型別提示覆蓋率：**90%+**

### 質化指標

- ✅ 程式碼更易讀
- ✅ 新功能更易新增
- ✅ Bug 更易修復
- ✅ 新貢獻者更易上手

---

## 💡 下一步行動

### 立即執行（今天）

1. ✅ 建立此重構計畫
2. ⏳ 開始 Task 1.1：分析 `image_preprocessor.py` 未覆蓋程式碼
3. ⏳ 建立 `plan_improve_image_preprocessor_coverage.md`

### 明天

4. 撰寫新測試
5. 驗證覆蓋率提升
6. 提交變更

---

*計畫建立時間：2024-12-13 22:42*  
*預計完成時間：2024-12-27（階段 1）*  
*負責人：AI Agent*
