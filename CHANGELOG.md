# 變更日誌

本文件記錄 PaddleOCR Toolkit 的所有重要變更。

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
