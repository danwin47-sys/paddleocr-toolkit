# 外掛開發指南

PaddleOCR Toolkit v1.2.0 外掛系統開發檔案。

---

## 📚 目錄

1. [快速開始](#快速開始)
2. [外掛型別](#外掛型別)
3. [生命週期](#生命週期)
4. [開發範例](#開發範例)
5. [最佳實踐](#最佳實踐)
6. [API 參考](#api-參考)

---

## 🚀 快速開始

### 建立第一個外掛

```python
from paddleocr_toolkit.plugins.base import OCRPlugin

class MyFirstPlugin(OCRPlugin):
    name = "My First Plugin"
    version = "1.0.0"
    author = "Your Name"
    description = "我的第一個 OCR 外掛"
    
    def on_init(self):
        """外掛初始化"""
        self.logger.info("外掛已初始化")
        return True
    
    def on_before_ocr(self, image):
        """OCR 前處理"""
        # 處理圖片
        return image
    
    def on_after_ocr(self, results):
        """OCR 後處理"""
        # 處理結果
        return results
```

### 使用外掛

```python
from paddleocr_toolkit.plugins.loader import PluginLoader

# 建立載入器
loader = PluginLoader('plugins/')

# 載入所有外掛
loader.load_all_plugins()

# 取得外掛
plugin = loader.get_plugin('My First Plugin')

# 使用外掛
processed_image = plugin.process_before_ocr(image)
processed_results = plugin.process_after_ocr(results)
```

---

## 🔧 外掛型別

### 1. 完整功能外掛

繼承 `OCRPlugin`，實作所有鉤子：

```python
from paddleocr_toolkit.plugins.base import OCRPlugin

class FullFeaturedPlugin(OCRPlugin):
    def on_init(self): ...
    def on_before_ocr(self, image): ...
    def on_after_ocr(self, results): ...
    def on_error(self, error): ...
    def on_shutdown(self): ...
```

### 2. 預處理外掛

僅處理輸入圖片：

```python
from paddleocr_toolkit.plugins.base import PreprocessorPlugin

class ImageProcessor(PreprocessorPlugin):
    def on_init(self): ...
    def on_before_ocr(self, image):
        # 只需實作此方法
        return processed_image
```

### 3. 後處理外掛

僅處理 OCR 結果：

```python
from paddleocr_toolkit.plugins.base import PostprocessorPlugin

class ResultProcessor(PostprocessorPlugin):
    def on_init(self): ...
    def on_after_ocr(self, results):
        # 只需實作此方法
        return processed_results
```

---

## 🔄 生命週期

外掛的完整生命週期：

```
1. 建立例項
   ↓
2. on_init() - 初始化
   ↓
3. on_before_ocr() - 預處理（每次 OCR 前）
   ↓
4. [OCR 處理]
   ↓
5. on_after_ocr() - 後處理（每次 OCR 後）
   ↓
6. on_error() - 錯誤處理（如有錯誤）
   ↓
7. on_shutdown() - 清理資源
```

---

## 💡 開發範例

### 範例 1：圖片降噪外掛

```python
from paddleocr_toolkit.plugins.base import PreprocessorPlugin
import cv2

class DenoisePlugin(PreprocessorPlugin):
    name = "Image Denoiser"
    version = "1.0.0"
    
    def on_init(self):
        self.strength = self.config.get('strength', 10)
        return True
    
    def on_before_ocr(self, image):
        # 使用 OpenCV 降噪
        denoised = cv2.fastNlMeansDenoising(
            image, 
            None, 
            self.strength
        )
        return denoised
```

### 範例 2：文字格式化外掛

```python
from paddleocr_toolkit.plugins.base import PostprocessorPlugin

class TextFormatterPlugin(PostprocessorPlugin):
    name = "Text Formatter"
    version = "1.0.0"
    
    def on_init(self):
        self.uppercase = self.config.get('uppercase', False)
        return True
    
    def on_after_ocr(self, results):
        if isinstance(results, str):
            text = results
            if self.uppercase:
                text = text.upper()
            return text
        return results
```

### 範例 3：效能監控外掛

```python
from paddleocr_toolkit.plugins.base import OCRPlugin
import time

class PerformanceMonitor(OCRPlugin):
    name = "Performance Monitor"
    version = "1.0.0"
    
    def on_init(self):
        self.timings = []
        return True
    
    def on_before_ocr(self, image):
        self.start_time = time.time()
        return image
    
    def on_after_ocr(self, results):
        elapsed = time.time() - self.start_time
        self.timings.append(elapsed)
        self.logger.info(f"處理耗時: {elapsed:.3f} 秒")
        return results
    
    def get_average_time(self):
        return sum(self.timings) / len(self.timings)
```

---

## ✨ 最佳實踐

### 1. 設定管理

使用 `self.config` 接收設定：

```python
def on_init(self):
    # 讀取設定，提供預設值
    self.param1 = self.config.get('param1', default_value)
    self.param2 = self.config.get('param2', default_value)
    return True
```

### 2. 日誌記錄

使用 `self.logger` 記錄日誌：

```python
self.logger.debug("除錯訊息")
self.logger.info("資訊訊息")
self.logger.warning("警告訊息")
self.logger.error("錯誤訊息")
```

### 3. 錯誤處理

妥善處理異常：

```python
def on_before_ocr(self, image):
    try:
        # 處理邏輯
        return processed_image
    except Exception as e:
        self.logger.error(f"處理失敗: {e}")
        # 返回原圖，避免中斷流程
        return image
```

### 4. 資源清理

在 `on_shutdown()` 中清理資源：

```python
def on_shutdown(self):
    # 關閉檔案
    if hasattr(self, 'file'):
        self.file.close()
    
    # 釋放記憶體
    if hasattr(self, 'large_data'):
        del self.large_data
    
    self.logger.info("資源已清理")
```

### 5. 型別檢查

處理多種輸入型別：

```python
def on_after_ocr(self, results):
    if isinstance(results, str):
        # 處理字串
        return self.process_string(results)
    elif isinstance(results, list):
        # 處理列表
        return [self.process_item(item) for item in results]
    elif isinstance(results, dict):
        # 處理字典
        return self.process_dict(results)
    return results
```

---

## 📖 API 參考

### OCRPlugin 基類

#### 屬性

```python
name: str           # 外掛名稱
version: str        # 版本號
author: str         # 作者
description: str    # 描述
config: Dict        # 設定字典
logger: Logger      # 日誌記錄器
enabled: bool       # 是否啟用
```

#### 方法

```python
on_init() -> bool
    初始化外掛
    返回: 是否成功

on_before_ocr(image) -> Any
    OCR 前處理
    引數: image - 輸入圖片
    返回: 處理後的圖片

on_after_ocr(results) -> Any
    OCR 後處理
    引數: results - OCR 結果
    返回: 處理後的結果

on_error(error: Exception) -> None
    錯誤處理
    引數: error - 異常物件

on_shutdown() -> None
    關閉清理

get_info() -> Dict
    取得外掛資訊

enable() -> None
    啟用外掛

disable() -> None
    停用外掛
```

### PluginLoader 載入器

#### 方法

```python
discover_plugins() -> List[str]
    發現外掛檔案

load_plugin_from_file(file_path: str) -> Optional[OCRPlugin]
    從檔案載入外掛

load_all_plugins() -> int
    載入所有外掛

get_plugin(name: str) -> Optional[OCRPlugin]
    取得指定外掛

get_all_plugins() -> Dict[str, OCRPlugin]
    取得所有外掛

enable_plugin(name: str) -> bool
    啟用外掛

disable_plugin(name: str) -> bool
    停用外掛

unload_plugin(name: str) -> bool
    解除安裝外掛

list_plugins() -> List[Dict]
    列出所有外掛資訊
```

---

## 🎯 進階主題

### 外掛間通訊

```python
class CommunicatingPlugin(OCRPlugin):
    def on_init(self):
        # 取得其他外掛
        self.other_plugin = self.get_other_plugin('Other Plugin Name')
        return True
    
    def on_after_ocr(self, results):
        # 使用其他外掛的功能
        if self.other_plugin:
            extra_data = self.other_plugin.get_some_data()
        return results
```

### 設定檔案

建立 `plugin_config.yaml`：

```yaml
image_enhancer:
  enhance_contrast: true
  sharpen: true
  denoise: false

text_cleaner:
  remove_special_chars: true
  fix_common_errors: true

statistics:
  collect_timing: true
  save_to_file: true
```

載入設定：

```python
import yaml

with open('plugin_config.yaml') as f:
    configs = yaml.safe_load(f)

loader = PluginLoader('plugins/')
for name, config in configs.items():
    plugin = loader.get_plugin(name)
    if plugin:
        plugin.config.update(config)
```

---

## 🔍 除錯技巧

### 1. 啟用除錯日誌

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

### 2. 測試單個外掛

```python
# 單獨測試外掛
plugin = MyPlugin(config={'debug': True})
plugin.initialize()

# 測試前處理
result = plugin.process_before_ocr(test_image)
assert result is not None

# 測試後處理
result = plugin.process_after_ocr(test_results)
assert result is not None
```

### 3. 使用斷言

```python
def on_before_ocr(self, image):
    assert image is not None, "圖片不能為 None"
    assert len(image.shape) == 3, "圖片必須是彩色"
    # 處理...
```

---

## 📦 發布外掛

### 1. 建立 `setup.py`

```python
from setuptools import setup

setup(
    name='my-ocr-plugin',
    version='1.0.0',
    py_modules=['my_plugin'],
    install_requires=[
        'paddleocr-toolkit>=1.2.0'
    ]
)
```

### 2. 打包

```bash
python setup.py sdist bdist_wheel
```

### 3. 分享

將外掛分享到外掛市場或 GitHub。

---

## 🆘 常見問題

### Q: 外掛沒有被載入？

A: 檢查：

1. 檔案是否在正確的目錄
2. 類別是否繼承 `OCRPlugin`
3. `on_init()` 是否返回 `True`

### Q: 如何除錯外掛？

A: 使用日誌：

```python
self.logger.debug(f"變數值: {value}")
```

### Q: 外掛間如何共享資料？

A: 使用類變數或設定系統：

```python
class MyPlugin(OCRPlugin):
    shared_data = {}  # 類變數，所有例項共享
```

---

**更多範例**: [plugins/](../plugins/)  
**問題回報**: [GitHub Issues](https://github.com/danwin47-sys/paddleocr-toolkit/issues)
