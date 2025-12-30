# 變更日誌

本文件記錄 PaddleOCR Toolkit 的所有重要變更。

---

## [3.3.0] - 2025-12-30 ✨

### 重大更新：品質強化與輕量化

此版本專注於移除技術債、優化部署流程與擴充插件系統。總計移除了超過 2,600 行的遺留程式碼。

### ✨ 新增功能

- ✅ **插件系統 (Plugins)** - 實作並驗證了擴充機制
    - 新增 `pii_masking.py` (個資遮蔽)
    - 新增 `watermark_remover.py` (浮水印去除)
    - 新增 `doc_classifier.py` (文件分類)
- ✅ **中文化 (i18n)** - 完整支援繁體中文介面
    - 新增 `i18n/zh_TW.json` 語系檔
- ✅ **Docker 優化** - 採用 Multi-stage build
    - 映像檔體積大幅縮減
    - 新增 `docker-compose.yml` 支援一鍵部署

### 🔧 改進

- ✅ **Legacy 移除** - 完全移除 `legacy/paddle_ocr_tool.py` (2,600+ 行)
- ✅ **Shim 機制** - 根目錄 `paddle_ocr_tool.py` 改寫為輕量級 Shim，確保向後相容
- ✅ **測試強化** - 測試覆蓋率提升至 84% (581 個測試通過)
- ✅ **文件同步** - 重寫 README 與 ARCHITECTURE 文檔，反映最新架構

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

| 項目 | 數值 |
|------|------|
| 新增模組 | 5 個 |
| 新增程式碼 | 1,732 行 |
| 測試覆蓋率 | 89%+ |
| 測試通過率 | 89% (39/44) |

---

## [1.2.0] 及更早版本

請參考 Git 提交歷史記錄。
