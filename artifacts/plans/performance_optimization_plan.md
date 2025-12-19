# 記憶體與 I/O 最佳化計畫

> **日期**: 2024-12-14  
> **目標**: 減少 70% 記憶體使用 + 提升 50% I/O 速度  
> **預計時間**: 3-4 小時

---

## 🎯 當前問題分析

### 記憶體問題

#### 問題 1: pixmap_to_numpy 強制複製

**位置**: `paddleocr_toolkit/core/pdf_utils.py:48`

```python
if copy:
    img_array = img_array.copy()  # 每次都複製！
```

**影響**: 100 頁 PDF × 20MB/頁 = 2GB 記憶體
**解決**: 使用生成器模式，不保留所有影象

#### 問題 2: batch_processor 一次載入所有頁面

**位置**: `paddleocr_toolkit/processors/batch_processor.py`

```python
results = []
for future in as_completed(futures):
    results.append(future.result())  # 累積所有結果
return results  # 全部返回！
```

**影響**: 記憶體持續累積
**解決**: 使用生成器逐頁返回

#### 問題 3: PDF 檔案未及時關閉

**位置**: 多處

```python
pdf_doc = fitz.open(pdf_path)
# ... 處理 ...
# 忘記 close() 或延遲關閉
```

**影響**: 檔案控制程式碼洩漏
**解決**: 使用 context manager

---

### I/O 問題

#### 問題 1: 頻繁小寫入

**影響**: 文字輸出時每行都寫入
**解決**: 批次緩衝寫入

#### 問題 2: 無緩衝讀寫

**影響**: 預設緩衝區太小
**解決**: 增加緩衝區大小

#### 問題 3: 重複轉換 PDF

**影響**: 相同頁面多次轉換
**解決**: 新增快取機制

---

## 📋 最佳化任務清單

### Phase 1: 記憶體最佳化

#### Task 1.1: PDF 處理生成器化

- [ ] 修改 `pdf_to_images_parallel` 為生成器
- [ ] 新增 `pdf_to_images_generator` 函式
- [ ] 使用 `yield` 逐頁返回結果

#### Task 1.2: 新增 context manager

- [ ] 為 PDF 檔案新增 `with` 支援
- [ ] 確保自動資源釋放
- [ ] 新增 `__enter__` 和 `__exit__`

#### Task 1.3: 最佳化 pixmap 處理

- [ ] 新增 `copy=False` 選項支援
- [ ] 在不需要保留時避免復製
- [ ] 及時釋放 pixmap 資源

#### Task 1.4: 串流處理

- [ ] 修改主處理迴圈為串流模式
- [ ] 處理完一頁立即釋放
- [ ] 新增垃圾回收提示

---

### Phase 2: I/O 最佳化

#### Task 2.1: 批次寫入

- [ ] 實現帶緩衝的檔案寫入器
- [ ] 批次累積後一次寫入
- [ ] 新增自動 flush 機制

#### Task 2.2: 增加緩衝區

- [ ] 設定大緩衝區（1MB）
- [ ] 最佳化檔案開啟引數
- [ ] 使用 `buffering` 引數

#### Task 2.3: 快取機制

- [ ] 新增 LRU 快取裝飾器
- [ ] 快取頁面轉換結果
- [ ] 快取文書處理結果

---

## 🔧 具體實現

### 1. 生成器模式

**新增檔案**: `paddleocr_toolkit/core/streaming_utils.py`

```python
def pdf_pages_generator(
    pdf_path: str,
    dpi: int = 150
) -> Generator[Tuple[int, np.ndarray], None, None]:
    """
    以生成器方式逐頁處理 PDF
    
    優點：
    - 記憶體使用固定（1 頁）
    - 支援大檔案處理
    - 自動資源管理
    """
    with fitz.open(pdf_path) as pdf_doc:
        for page_num in range(len(pdf_doc)):
            # 載入頁面
            page = pdf_doc[page_num]
            
            # 轉換為影象
            image = page_to_numpy(page, dpi=dpi, copy=False)
            
            # 返回結果
            yield (page_num, image)
            
            # 立即釋放
            del image
            del page

# 使用方式
for page_num, image in pdf_pages_generator(pdf_path):
    result = process(image)
    save(result)
    # image 自動釋放
```

### 2. 緩衝寫入器

**新增檔案**: `paddleocr_toolkit/core/buffered_writer.py`

```python
class BufferedWriter:
    """帶緩衝的檔案寫入器"""
    
    def __init__(self, filepath: str, buffer_size: int = 1000):
        self.filepath = filepath
        self.buffer = []
        self.buffer_size = buffer_size
        self.file = None
    
    def __enter__(self):
        self.file = open(
            self.filepath, 
            'w', 
            encoding='utf-8',
            buffering=1024*1024  # 1MB 緩衝
        )
        return self
    
    def write(self, text: str):
        """寫入文字（緩衝）"""
        self.buffer.append(text)
        
        if len(self.buffer) >= self.buffer_size:
            self.flush()
    
    def flush(self):
        """重新整理緩衝"""
        if self.buffer:
            self.file.write('\n'.join(self.buffer) + '\n')
            self.buffer.clear()
    
    def __exit__(self, *args):
        self.flush()
        if self.file:
            self.file.close()

# 使用方式
with BufferedWriter('output.txt') as writer:
    for line in lines:
        writer.write(line)  # 自動批次寫入
```

### 3. Context Manager for PDF

**修改檔案**: `paddleocr_toolkit/core/pdf_utils.py`

```python
from contextlib import contextmanager

@contextmanager
def open_pdf_context(pdf_path: str):
    """
    PDF 檔案 context manager
    
    確保資源自動釋放
    """
    pdf_doc = fitz.open(pdf_path)
    try:
        yield pdf_doc
    finally:
        pdf_doc.close()
        # 強制垃圾回收
        import gc
        gc.collect()

# 使用方式
with open_pdf_context(pdf_path) as pdf_doc:
    # 處理 PDF
    pass
# 自動關閉和釋放
```

### 4. LRU 快取

**修改檔案**: `paddleocr_toolkit/processors/text_processor.py`

```python
from functools import lru_cache

@lru_cache(maxsize=10000)
def fix_english_spacing(text: str) -> str:
    """
    修復英文空格（帶快取）
    
    相同文字直接返回快取結果
    """
    # ... 原有邏輯 ...
```

---

## 📊 預期效果

### 記憶體使用

| 場景 | 最佳化前 | 最佳化後 | 改善 |
|------|--------|--------|------|
| 10 頁 PDF | 200MB | 20MB | -90% |
| 100 頁 PDF | 2GB | 20MB | -99% |
| 1000 頁 PDF | OOM 💀 | 20MB | ✅ 可用 |

### I/O 效能

| 操作 | 最佳化前 | 最佳化後 | 改善 |
|------|--------|--------|------|
| 文字輸出 | 3.2s | 1.6s | +50% |
| JSON 輸出 | 2.8s | 1.4s | +50% |
| 重複處理 | 100% | 10% | +90% |

---

## 🧪 測試策略

### 記憶體測試

```python
import tracemalloc

def test_memory_usage():
    tracemalloc.start()
    
    # 處理 100 頁 PDF
    process_pdf('large.pdf')
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # 峰值記憶體應 < 50MB
    assert peak < 50 * 1024 * 1024
```

### I/O 測試

```python
import time

def test_io_speed():
    start = time.time()
    
    # 寫入 10000 行
    save_text_output('test.txt', lines)
    
    elapsed = time.time() - start
    
    # 應 < 2 秒
    assert elapsed < 2.0
```

---

## 📅 執行計畫

### 時間分配

| Phase | 任務 | 時間 |
|-------|------|------|
| **Phase 1** | 記憶體最佳化 | 2 小時 |
| ↳ Task 1.1 | 生成器化 | 45 min |
| ↳ Task 1.2 | Context manager | 30 min |
| ↳ Task 1.3 | Pixmap 最佳化 | 30 min |
| ↳ Task 1.4 | 串流處理 | 15 min |
| **Phase 2** | I/O 最佳化 | 1 小時 |
| ↳ Task 2.1 | 批次寫入 | 30 min |
| ↳ Task 2.2 | 緩衝區 | 15 min |
| ↳ Task 2.3 | 快取 | 15 min |
| **Phase 3** | 測試驗證 | 1 小時 |
| **總計** | | **4 小時** |

---

## ✅ 驗收標準

### 必須達成

- [ ] 峰值記憶體 < 50MB（100 頁 PDF）
- [ ] 可處理 1000 頁 PDF 不 OOM
- [ ] I/O 速度提升 > 40%
- [ ] 所有測試透過
- [ ] 無功能回退

### 期望達成

- [ ] 記憶體減少 > 70%
- [ ] I/O 速度提升 > 50%
- [ ] 重複處理快 > 90%
- [ ] 程式碼更清晰

---

*計畫建立時間: 2024-12-14 13:00*  
*預計完成時間: 2024-12-14 17:00*  
*狀態: 待執行*
