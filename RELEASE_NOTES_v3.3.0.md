# PaddleOCR Toolkit v3.3.0 Release Notes 🎉

**Release Date**: 2026-01-03  
**Type**: Major Quality & Stability Update

---

## 🎯 版本亮點

v3.3.0 是一個里程碑版本，達成企業級品質標準：

- ✅ **90% 測試覆蓋率** - 從 84% 提升，新增 208 個測試
- ✅ **789 測試全數通過** - 100% 通過率，0 失敗，0 跳過
- ✅ **CI/CD 完全穩定** - 支援 Python 3.8-3.12 全版本
- ✅ **企業級代碼品質** - Flake8 合規，Black 格式化，100% 類型提示

---

## ✨ 主要新功能

### 🏥 系統監控 API

#### Health Check Endpoint
**GET /health** 或 **GET /api/health**

提供完整的系統健康狀態檢查：
- ✅ 版本資訊與運行時間追蹤
- ✅ 組件狀態檢查（OCR引擎、WebSocket、檔案系統、任務佇列）
- ✅ 即時統計數據（任務數、連接數）

```json
{
  "status": "healthy",
  "version": "3.3.0",
  "uptime_seconds": 1234.56,
  "components": {
    "ocr_engine": "ready",
    "websocket": "active",
    "file_system": "ok",
    "task_queue": "active"
  },
  "stats": {
    "total_tasks": 10,
    "active_ws_connections": 2
  }
}
```

#### System Metrics API
**GET /api/metrics**

詳細的系統資源監控：
- 📊 CPU 使用率與核心數追蹤
- 💾 記憶體使用情況（總量、可用量、進程使用）
- 💿 磁碟空間監控
- 📈 任務統計（總數、完成、處理中、錯誤）

#### Task Queue Status
**GET /api/queue/status**

任務佇列狀態監控：
- 📋 佇列大小與活動任務數
- 👥 工作者數量與處理統計

---

### 🔌 WebSocket 自動重連

智能重連機制確保連接穩定性：

- ⚡ **指數退避算法** - 1s → 2s → 4s → 8s → ... → 30s
- 🎨 **4 種連接狀態**：
  - 🟡 Connecting - 連接中
  - 🟢 Connected - 已連接
  - 🟠 Reconnecting - 重連中
  - 🔴 Disconnected - 已斷開
- 🔘 **手動重連控制** - UI 提供重連按鈕

---

### ⚙️ 並發控制與任務管理

- 🚦 **任務佇列系統** - 限制同時處理的 OCR 任務數（可配置工作者數）
- 🏆 **優先級支援** - LOW / NORMAL / HIGH 三級任務優先級
- 📊 **統計追蹤** - 自動追蹤處理總數與失敗數

---

### 🧩 插件系統強化

擴充插件系統，提供更強大的定制能力：

**新增插件示例**：
- 🔒 **pii_masking.py** - 自動遮蔽身分證、手機號、Email
- 🎨 **watermark_remover.py** - 去除文件浮水印以提升 OCR 精度
- 📁 **doc_classifier.py** - 自動分類文件類型（發票/合約/報告）

**國際化支援**：
- 🌏 完整繁體中文介面 (`i18n/zh_TW.json`)

---

## 🔧 重大改進

### 📈 測試覆蓋率大幅提升 (+6%)

| 指標         | v3.2.0 | v3.3.0 | 改進 |
| ------------ | ------ | ------ | ---- |
| **覆蓋率**   | 84%    | 90%    | +6%  |
| **測試數量** | 581    | 789    | +208 |
| **通過率**   | 100%   | 100%   | -    |

**核心模組高覆蓋**：
- `core/config_loader.py` - **98%**
- `cli/mode_processor.py` - **96%**
- `llm/llm_client.py` - **95%**
- `cli/commands/benchmark.py` - **89%**
- `api/routers/ocr.py` - **84%**
- `processors/hybrid_processor.py` - **84%**

---

### 🛡️ CI/CD 管道完全穩定

修復了 **6 個主要 CI 問題**，確保在所有支援的 Python 版本上均能穩定運行：

| #   | 問題                        | 解決方案                        | Commit    |
| --- | --------------------------- | ------------------------------- | --------- |
| 1   | Python 3.11+ numpy 版本衝突 | 放寬 numpy 版本限制             | `326787b` |
| 2   | 缺少 psutil 依賴            | 補充至 requirements-ci.txt      | `610208c` |
| 3   | Flake8 lint 錯誤            | 清理無用 global、拆分超長行     | `c82a54a` |
| 4   | 缺少 Levenshtein 依賴       | 實作 optional import + fallback | `168f55b` |
| 5   | validate.py 語法錯誤        | 修復 difflib 邏輯               | `c722608` |
| 6   | Runtime 依賴缺失            | 添加 openpyxl、限制 numpy<2.0.0 | `8860b17` |

**支援的 Python 版本**：
- ✅ Python 3.8
- ✅ Python 3.9
- ✅ Python 3.10
- ✅ Python 3.11
- ✅ Python 3.12

---

### ✨ 程式碼品質提升

- ✅ **Flake8 全面合規** - 所有 lint 警告與錯誤已清理
- ✅ **類型提示完整** - 100% 函數簽名包含類型註解
- ✅ **Black 格式化** - 全專案統一代碼風格（88 個文件）
- ✅ **Legacy 移除** - 完全移除 `legacy/paddle_ocr_tool.py` (2,600+ 行)
- ✅ **Shim 機制** - 確保 100% 向後相容

---

## 🐛 修復問題

### CI/CD 修復
- 修復 Python 3.11+ 環境下的 numpy ABI 不相容問題
- 修復缺少 psutil 導致的 5 個測試文件 collection 失敗
- 修復缺少 openpyxl 導致的 Excel 導出測試失敗
- 修復 numpy.core.multiarray import 錯誤

### 代碼修復
- 修復 `api/main.py` 未使用的 global 聲明
- 修復 `hybrid_processor.py` 超長行 lint 錯誤
- 修復 `validate.py` 語法錯誤與 difflib 邏輯

### 依賴管理
- 完善 `requirements-ci.txt` 確保 CI 環境一致性
- 實作 Levenshtein optional import 機制提升相容性

---

## 📊 統計數據

### 程式碼規模
- **總行數**: 15,000+ 行（不含註解與空行）
- **核心模組**: 8 個主要模組
- **處理器**: 10+ 個專業處理器
- **API 端點**: 20+ 個 RESTful API

### 測試指標
- **單元測試**: 789 個（100% 通過）
- **覆蓋率**: 90%（企業級標準）
- **CI/CD**: ✅ 所有檢查通過

### 文件完整性
- **專業文檔**: 26 個 Markdown 文件
- **程式碼註解**: 100% 文檔字串覆蓋
- **類型提示**: 100% 函數簽名

---

## 📦 安裝與升級

### 從 PyPI 安裝（推薦）
```bash
pip install paddleocr-toolkit==3.3.0
```

### 從原始碼安裝
```bash
git clone https://github.com/danwin47-sys/paddleocr-toolkit.git
cd paddleocr-toolkit
git checkout v3.3.0
pip install -r requirements.txt
```

### 升級現有版本
```bash
pip install --upgrade paddleocr-toolkit==3.3.0
```

---

## ⚠️ 破壞性變更

**無** - 本版本維持 **100% 向後相容**

所有現有的 API、CLI 命令、配置文件均保持相容。舊版本代碼可無縫升級。

---

## 🔗 相關文件

- 📖 [完整變更日誌](https://github.com/danwin47-sys/paddleocr-toolkit/blob/master/CHANGELOG.md)
- 📚 [使用者指南](https://github.com/danwin47-sys/paddleocr-toolkit/blob/master/docs/USER_GUIDE.md)
- 🔌 [API 文件](https://github.com/danwin47-sys/paddleocr-toolkit/blob/master/docs/API.md)
- 🤝 [貢獻指南](https://github.com/danwin47-sys/paddleocr-toolkit/blob/master/docs/CONTRIBUTING.md)
- 🏗️ [架構說明](https://github.com/danwin47-sys/paddleocr-toolkit/blob/master/docs/ARCHITECTURE.md)

---

## 🙏 致謝

感謝所有使用者的回饋與支持！本版本的品質提升得益於社群的寶貴意見。

特別感謝：
- PaddleOCR 團隊提供強大的 OCR 引擎
- 所有提出 Issue 和 Pull Request 的貢獻者
- 測試用戶提供的實際使用場景反饋

---

## 📞 聯絡方式

- **GitHub**: https://github.com/danwin47-sys/paddleocr-toolkit
- **Issues**: https://github.com/danwin47-sys/paddleocr-toolkit/issues
- **Discussions**: https://github.com/danwin47-sys/paddleocr-toolkit/discussions

---

**Happy OCR Processing! 🚀**
