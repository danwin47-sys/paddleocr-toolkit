# Custom Directory

此目錄用於存放使用者自訂的內容，例如：

- 自訂插件
- 自訂設定檔
- 自訂術語表
- 其他擴展功能

## 使用方式

請將您的自訂模組放入此目錄，並在程式中引用。

```python
from custom.my_plugin import MyPlugin
```

---

**注意**：此目錄內容不會被 Git 追蹤（已加入 .gitignore）。
