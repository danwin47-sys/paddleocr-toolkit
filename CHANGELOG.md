# 變更日誌

本文件記錄 PaddleOCR Toolkit 的所有重要變更。

---

## [3.4.0] - 2026-01-04 🚀

### 重大更新：Python 3.12 環境完整遷移

此版本成功將專案從 Python 3.7 遷移至 Python 3.12，解決所有依賴相容性問題，修復 API 不相容，並大幅提升測試效能。**正式棄用 Python 3.7 支援**。

### ⚠️ 破壞性變更

- **Python 版本要求**: 現在需要 **Python 3.8+** (建議 3.10+)
- **棄用 Python 3.7**: 不再支援 Python 3.7，請升級至 3.8 或更新版本

  - `paddlepaddle==2.6.2`
  - `paddleocr==2.8.1`
  - `pytest-asyncio==0.25.2`
  - `setuptools==80.9.0`
- ✅ **測試優化** - AsyncIO 測試完全支援

### 🐛 問題修復

#### 1. PPStructure API 相容性修復
- **問題**: `'PPStructure' object has no attribute 'predict'`
- **修復**: 更新 `ocr_engine.py` 優先使用 `__call__` 方法
- **影響**: 混合模式 OCR 現在正常運作

#### 2. 異步任務隊列導入錯誤修復
- **問題**: 多進程 worker 中 PaddleOCR 導入失敗但錯誤被靜默
- **修復**: 增強 `ocr.py` 和 `parallel_pdf_processor.py` 錯誤處理
- **影響**: 詳細錯誤日誌幫助快速診斷問題

#### 3. JSON 序列化錯誤修復
- **問題**: `PydanticSerializationError: Unable to serialize numpy.ndarray`
- **修復**: 添加 `convert_to_serializable()` 遞迴轉換函數
- **影響**: 前端現在能正確顯示 OCR 結果

### 🔧 改進

#### 測試與 CI/CD
- ✅ **測試通過率**: 789/791 (99.7%)
- ✅ **測試覆蓋率**: 89% (超過要求的 76%)
- ✅ **執行速度**: 提升 **50%** (23.39s vs 46.84s)
- ✅ **CI/CD**: 全部 9 項檢查通過

#### 配置更新
- ✅ 更新 `setup.py`: `python_requires='>=3.8'`
- ✅ 更新 CI 配置: 移除 Python 3.12 錯誤容忍
- ✅ 更新 `README.md`: 新增系統需求章節

### 📊 效能提升

| 指標         | 改善         |
| ------------ | ------------ |
| 測試執行時間 | **50% 更快** |
| 測試通過數   | +30 測試     |
| 代碼覆蓋率   | +3%          |

### 📝 文件更新

- ✅ 新增 Python 3.12 設定指南
- ✅ 新增完整遷移報告 (walkthrough.md)
- ✅ 更新 README 系統需求
- ✅ 更新 CHANGELOG 與 Release Notes

### 🔗 相關連結

- [Python 3.12 遷移報告](docs/python312_migration.md)
- [測試覆蓋率報告](docs/python312_coverage_report.md)

---

## [3.5.0] - 2026-01-02

### 改進 🔧
- 📝 **日誌標準化**: 完成全系統日誌重構 (Phases 1-8)
  - 統一使用 `paddleocr_toolkit.utils.logger`
  - 移除了 360+ 個遺留的 `print()` 語句
  - 支援 `LOG_LEVEL` 環境變數控制
- 🏗️ **前端架構**: 統一使用 `web-frontend/` 並配置靜態導出
- ⚙️ **配置管理**: 引入 `Settings` 類別集中管理配置
- 🧹 **代碼清理**: 移除了所有 TODO 項目與過時的註解

---
## [3.4.0] - 2025-12-31

### 新增 ✨
- 🎨 **全新 Clean Slate UI**：從暗色玻璃擬態改為明亮極簡風格
  - 重寫 `globals.css`，建立完整的設計系統（變數、排版、間距）
  - 語意化 CSS 類別（`.app-sidebar`, `.upload-zone`, `.modal-overlay` 等）
  - 支援明亮模式，提升可讀性與專業感
- 📊 **Google Analytics 整合**：追蹤使用者行為與關鍵事件

### 改進 ��
- ⚡ **模型管理優化**：新增 `preload_models.py` 腳本
- 🐛 **問題修復**：修復 Hybrid 模式首次執行卡住問題、Settings Modal z-index 重疊問題
- 🧹 **程式碼清理**：移除 DEBUG 標籤和除錯面板

### 變更 🔧
- 重構所有主要 React 元件使用新設計系統
- 移除舊的「假 Tailwind」utility classes

---


## [3.3.0] - 2026-01-03 ✨

### 重大更新：企業級品質認證版本

此版本達成重要里程碑：**90% 測試覆蓋率**與**完全穩定的 CI/CD 管道**。專注於測試強化、程式碼品質提升，並完成了系統性的 CI/CD 優化，確保在所有支援的 Python 版本上均能穩定運行。

### ✨ 新增功能

#### 系統監控與健康檢查
- ✅ **Health Check API** - `/health` 與 `/api/health` 端點
    - 版本資訊與運行時間追蹤
    - 組件狀態檢查（OCR 引擎、WebSocket、檔案系統、任務佇列）
    - 即時統計數據（任務數、連接數）
- ✅ **System Metrics API** - `/api/metrics` 資源監控
    - CPU 使用率與核心數追蹤
    - 記憶體使用情況（總量、可用量、進程使用）
    - 磁碟空間監控
    - 任務統計（總數、完成、處理中、錯誤）
- ✅ **Task Queue API** - `/api/queue/status` 佇列狀態
    - 佇列大小與活動任務數
    - 工作者數量與處理統計

#### WebSocket 自動重連
- ✅ **智能重連機制** - 指數退避算法（1s → 2s → 4s → ... → 30s）
- ✅ **連接狀態管理** - 4 種視覺化狀態（連接中、已連接、重連中、已斷開）
- ✅ **手動重連控制** - 提供重連按鈕支援手動操作

#### 並發控制與任務管理
- ✅ **任務佇列系統** - 限制同時處理的 OCR 任務數（預設 2 個工作者）
- ✅ **優先級支援** - 支援任務優先級設定（LOW/NORMAL/HIGH）
- ✅ **統計追蹤** - 追蹤處理總數與失敗數

#### 插件系統強化
- ✅ **插件生態完善** - 實作並驗證了擴充機制
    - 新增 `pii_masking.py` (個資遮蔽)
    - 新增 `watermark_remover.py` (浮水印去除)
    - 新增 `doc_classifier.py` (文件分類)
- ✅ **中文化 (i18n)** - 完整支援繁體中文介面
    - 新增 `i18n/zh_TW.json` 語系檔

### 🔧 改進

#### 測試覆蓋率大幅提升 (+6%)
- ✅ **90% 全專案測試覆蓋率** - 從 84% 提升至 90%
- ✅ **789 個單元測試** - 新增 208 個測試案例（從 581 增至 789）
- ✅ **100% 測試通過率** - 所有測試均通過，無跳過或失敗
- ✅ **核心模組高覆蓋** - 關鍵模組達 95%+ 覆蓋率
    - `core/config_loader.py` (98%)
    - `cli/mode_processor.py` (96%)
    - `llm/llm_client.py` (95%)
    - `cli/commands/benchmark.py` (89%)
    - `api/routers/ocr.py` (84%)
    - `processors/hybrid_processor.py` (84%)

#### CI/CD 管道完全穩定
- ✅ **6 個主要 CI 問題修復**
    1. Python 3.11+ numpy 版本衝突 → 放寬版本限制
    2. 缺少 psutil 依賴 → 補充至 requirements-ci.txt
    3. Flake8 lint 錯誤 → 清理無用 global、拆分超長行
    4. 缺少 Levenshtein 依賴 → 實作 optional import + fallback
    5. validate.py 語法錯誤 → 修復 difflib 邏輯
    6. Runtime 依賴缺失 → 添加 openpyxl、限制 numpy<2.0.0
- ✅ **全版本 Python 支援** - Python 3.8, 3.9, 3.10, 3.11, 3.12
- ✅ **依賴管理優化** - 完善 requirements-ci.txt 確保環境一致性

#### 程式碼品質提升
- ✅ **Flake8 全面合規** - 清理所有 lint 警告與錯誤
- ✅ **類型提示完整** - 100% 函數簽名包含類型註解
- ✅ **Black 格式化** - 全專案統一代碼風格
- ✅ **Legacy 移除** - 完全移除 `legacy/paddle_ocr_tool.py` (2,600+ 行)
- ✅ **Shim 機制** - 根目錄 `paddle_ocr_tool.py` 改寫為輕量級 Shim，確保向後相容

#### 文件完善
- ✅ **README 更新** - 反映最新功能與統計數據
- ✅ **CHANGELOG 完善** - 詳細記錄所有變更
- ✅ **Release Notes** - 準備專業的 GitHub Release 文件
- ✅ **文件同步** - 所有文檔與 v3.3.0 版本保持一致

---

## [3.2.0] - 2025-12-20 💎

### 重大更新：企業級生產力與 Web 儀表板

這是 PaddleOCR Toolkit 的一個里程碑版本，將其從命令列工具轉化為一個具備完整 Web 生態與 AI 勘誤能力的企業級系統。

### ✨ 新增功能

- ✅ **Web 儀表板 (Glassmorphism)** - 全新的玻璃擬態現代介面
    - 支援多檔案拖放批次處理對列
    - 整合分頁結果預覽與詳細 OCR 信心度顯示
    - 響應式佈局 (RWD)，完美適配行動端
- ✅ **雙頂級 LLM 支援** - 同時整合 Gemini 3 Flash 與 Claude 3.5 Sonnet
    - 具備語義自動糾偏與深度理解能力
    - 客戶端金鑰管理機制，兼顧隱私與便利性
- ✅ **並行文件處理** - 正式實作並行 PDF 處理器
    - 利用多核心 CPU 大幅提升大型 PDF 解析效率
- ✅ **智慧 OCR 快取** - 基於雜湊的快取機制，相同檔案重複處理時秒速返回，節省 Token 成本
- ✅ **專業報表匯出** - 支援將辨識結果直接匯出為 Word (.docx) 與 Excel (.xlsx)

### 🔧 改進

- ✅ **API 穩定性** - `file_manager` 單元測試覆蓋率達到 100%
- ✅ **安裝簡化** - 更新 `setup.py` 與 `requirements.txt` 以支援一鍵部署所有擴展功能
- ✅ **環境適配** - 解決 CI 測試中的依賴衝突與編碼警告問題

---

## [3.0.0] - 2025-12-18 🚀

### 重大更新：AI 驅動的語義處理增強

引入了基於 LLM 的語義處理器，徹底改進 OCR 後處理能力。

### ✨ 新增功能

- ✅ **SemanticProcessor** - 基於 LLM (Ollama/OpenAI) 的語義分析
    - 自動 OCR 錯誤修正（準確率提升 15%+）
    - 結構化資料提取（從 OCR 文本自動生成 JSON）
    - 文件摘要生成
- ✅ **中英繁體優化** - 專門針對繁體中文 OCR 修正的提示詞優化
- ✅ **Facade 整合** - `PaddleOCRFacade` 新增 `enable_semantic` 參數與連動 API

### 🔧 改進

- ✅ 優化 `PaddleOCRFacade` 介面，支援語義處理公開方法
- ✅ 建立 `llm` 模組，模組化 LLM 客戶端實現
- ✅ 更新 `docs/SEMANTIC_PROCESSOR_GUIDE.md` 指南

---

## [2.0.0] - 2025-12-18 🎉

### 重大更新：模組化架構重構

這是一個**重大版本更新**，將整個專案從單體架構重構為模組化架構。

### ✨ 新增功能

#### 核心 Processors
- ✅ **HybridPDFProcessor** (540 行) - 混合模式處理
- ✅ **EnhancedTranslationProcessor** (400 行) - 翻譯流程管理
- ✅ **BasicProcessor** (284 行) - 基本 OCR 模式
- ✅ **DecoupledModeProcessor** (243 行) - CLI 層解耦
- ✅ **PaddleOCRFacade** (265 行) - 輕量 API 層

#### 文件
- `FACADE_API_GUIDE.md` - 新 API 使用指南
- `MIGRATION_GUIDE.md` - 完整遷移指南
- `TESTING_GUIDE.md` - 測試指南

### 🔧 改進

- ✅ 消除循環依賴
- ✅ 測試覆蓋率 76% → **89%+**
- ✅ 主檔案 2,690 行 → 265 行（-90%）
- ✅ 5 個專業模組（1,732 行）

### 🔄 變更

- 推薦使用 `PaddleOCRFacade` 替代 `PaddleOCRTool`
- 100% 向後相容

### ⚠️ 破壞性變更

**無**！本版本保持 100% 向後相容。

### 📊 統計

| 項目       | 數值        |
| ---------- | ----------- |
| 新增模組   | 5 個        |
| 新增程式碼 | 1,732 行    |
| 測試覆蓋率 | 89%+        |
| 測試通過率 | 89% (39/44) |

---

## [1.2.0] 及更早版本

請參考 Git 提交歷史記錄。
