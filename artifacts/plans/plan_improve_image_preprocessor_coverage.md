# Task 1.1: 提升 image_preprocessor.py 測試覆蓋率

> 建立時間：2024-12-13 22:45  
> 狀態：⏳ 執行中  
> 當前覆蓋率：66%  
> 目標覆蓋率：75%+

---

## 📊 覆蓋率分析

### 當前狀態

- **總行數**：95 行
- **未覆蓋**：32 行
- **覆蓋率**：66%
- **現有測試**：19 個

### 未覆蓋的程式碼行

#### 1. Import 錯誤處理（行 14-15, 20-21）

```python
14: except ImportError:
15:    HAS_NUMPY = False

20: except ImportError:
21:     HAS_CV2 = False
```

**原因**：在測試環境中，numpy 和 cv2 都已安裝  
**需要**：Mock 缺少依賴的情況

---

#### 2. cv2 未安裝的警告（行 37-38, 70-71, 91-92, 125-126, 181）

```python
37: logging.warning("cv2 未安裝，跳過對比度增強")
38: return image
```

**原因**：測試環境有 cv2  
**需要**：Mock `HAS_CV2 = False` 的情況

---

#### 3. deskew() 特殊情況（行 132, 144-166）

```python
132: gray = image.copy()  # 灰階圖片分支

144-166: # 角度計算和旋轉邏輯
- 計算平均角度
- 過濾超出範圍的角度
- 角度太小不旋轉（< 0.5°）
- 實際旋轉
```

**原因**：現有測試只覆蓋基本情況  
**需要**：

- 測試灰階輸入
- 測試不同角度範圍
- 測試小角度不旋轉的情況

---

#### 4. binarize() 未測試的路徑（行 229）

```python
229: result = binarize(result)
```

**原因**：`preprocess_for_ocr()` 的 `binarize_img=True` 分支未測試  
**需要**：測試完整預處理管線

---

## 📋 需要新增的測試

### Test Suite 1: Import 錯誤處理

#### Test 1.1: 測試缺少 numpy

```python
def test_missing_numpy(monkeypatch):
    """測試缺少 numpy 時的行為"""
    # Mock HAS_NUMPY = False
    # 驗證函式正常返回原圖而非崩潰
```

#### Test 1.2: 測試缺少 cv2

```python
def test_missing_cv2(monkeypatch):
    """測試缺少 cv2 時的行為"""
    # Mock HAS_CV2 = False
    # 驗證所有函式都能優雅地處理
```

---

### Test Suite 2: deskew() 邊界條件

#### Test 2.1: 灰階圖片輸入

```python
def test_deskew_grayscale_input():
    """測試 deskew 處理灰階圖片"""
    gray_image = np.ones((100, 100), dtype=np.uint8) * 128
    result = deskew(gray_image)
    assert result.shape == gray_image.shape
```

#### Test 2.2: 小角度不旋轉

```python
def test_deskew_small_angle_no_rotation():
    """測試小於 0.5 度時不旋轉"""
    # 建立幾乎不傾斜的圖片
    # 驗證返回原圖
```

#### Test 2.3: 大角度超出範圍

```python
def test_deskew_angle_out_of_range():
    """測試角度超出 max_angle 時的處理"""
    # 建立傾斜很大的圖片
    # 驗證不會過度校正
```

#### Test 2.4: 角度計算邏輯

```python
def test_deskew_median_angle_calculation():
    """測試使用中位數計算平均角度"""
    # 需要有多條直線的圖片
    # 驗證角度計算正確
```

---

### Test Suite 3: sharpen() 未覆蓋分支

#### Test 3.1: 缺少 cv2 時的 sharpen

```python
def test_sharpen_without_cv2(monkeypatch):
    """測試缺少 cv2 時 sharpen 返回原圖"""
    monkeypatch.setattr("paddleocr_toolkit.processors.image_preprocessor.HAS_CV2", False)
    image = np.ones((100, 100, 3), dtype=np.uint8)
    result = sharpen(image)
    assert np.array_equal(result, image)
```

---

### Test Suite 4: preprocess_for_ocr() 完整管線

#### Test 4.1: 啟用二值化

```python
def test_preprocess_with_binarize():
    """測試啟用二值化的預處理"""
    image = create_test_image()
    result = preprocess_for_ocr(
        image,
        enhance=True,
        binarize_img=True  # 測試這個分支
    )
    assert result is not None
```

#### Test 4.2: 啟用所有選項

```python
def test_preprocess_all_options_enabled():
    """測試啟用所有預處理選項"""
    image = create_test_image()
    result = preprocess_for_ocr(
        image,
        enhance=True,
        denoise_img=True,
        deskew_img=True,
        binarize_img=True,
        sharpen_img=True
    )
    assert result is not None
```

---

## 🎯 實作策略

### 優先順序

1. **高優先順序**：deskew() 邊界條件（行 132, 144-166）
   - 估計提升：~10%
   - 風險：低
   - 工時：1 小時

2. **中優先順序**：preprocess_for_ocr() 完整管線（行 229）
   - 估計提升：~5%
   - 風險：低
   - 工時：30 分鐘

3. **低優先順序**：Import 錯誤處理（行 14-15, 20-21）
   - 估計提升：~5%
   - 風險：需要 monkeypatch
   - 工時：45 分鐘

### 預期覆蓋率提升

- 當前：66%
- 新增測試後：**75-78%**

---

## ✅ 執行步驟

### Step 1: 新增 deskew() 測試

- [ ] 測試灰階輸入
- [ ] 測試小角度不旋轉
- [ ] 測試角度計算邏輯
- [ ] 執行測試並驗證

### Step 2: 新增 preprocess_for_ocr() 測試

- [ ] 測試 binarize_img=True
- [ ] 測試所有選項啟用
- [ ] 執行測試並驗證

### Step 3: 新增錯誤處理測試

- [ ] Mock HAS_CV2 = False
- [ ] 測試所有函式的降級行為
- [ ] 執行測試並驗證

### Step 4: 驗證覆蓋率

```bash
pytest tests/test_image_preprocessor.py --cov=paddleocr_toolkit.processors.image_preprocessor --cov-report=term-missing
```

---

## 📝 測試程式碼範例

### 範例 1: deskew 灰階輸入

```python
def test_deskew_grayscale_input(self):
    """測試 deskew 處理灰階圖片"""
    # 建立灰階圖片
    gray_image = np.ones((100, 100), dtype=np.uint8) * 128
    
    # 執行 deskew
    result = deskew(gray_image)
    
    # 驗證
    assert result.shape == gray_image.shape
    assert len(result.shape) == 2  # 仍是灰階
```

### 範例 2: preprocess 啟用二值化

```python
def test_preprocess_with_binarize(self):
    """測試啟用二值化的預處理"""
    # 建立測試圖片
    image = np.ones((100, 100, 3), dtype=np.uint8) * 128
    
    # 執行預處理
    result = preprocess_for_ocr(
        image,
        enhance=True,
        binarize_img=True
    )
    
    # 驗證
    assert result is not None
    assert result.shape == image.shape
```

### 範例 3: Mock 缺少 cv2

```python
def test_functions_without_cv2(self, monkeypatch):
    """測試缺少 cv2 時的降級行為"""
    # Mock HAS_CV2 = False
    monkeypatch.setattr(
        "paddleocr_toolkit.processors.image_preprocessor.HAS_CV2",
        False
    )
    
    image = np.ones((100, 100, 3), dtype=np.uint8)
    
    # 測試所有函式都返回原圖
    assert np.array_equal(enhance_contrast(image), image)
    assert np.array_equal(denoise(image), image)
    assert np.array_equal(binarize(image), image)
    assert np.array_equal(deskew(image), image)
    assert np.array_equal(sharpen(image), image)
```

---

## 🎯 成功標準

- ✅ 覆蓋率從 66% 提升至 75%+
- ✅ 所有新測試透過
- ✅ 現有測試仍然透過
- ✅ 無新增 lint 錯誤

---

## 📅 時間規劃

- **開始時間**：2024-12-13 22:45
- **預計完成**：2024-12-13 23:30（45 分鐘）
- **實際工時**：待記錄

---

*計畫建立：2024-12-13 22:45*  
*執行狀態：⏳ 進行中*
