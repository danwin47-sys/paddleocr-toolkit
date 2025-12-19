# 發布說明 - v1.0.1

**發布日期**: 2024-12-15  
**狀態**: ✅ 準備發布

---

## 🎉 更新亮點

### v1.1.0 - 品質與檔案更新版本

此版本專注於提升測試覆蓋率、完善檔案以及改善開發者體驗。

#### 📊 測試改善 (第 1 週)

- **新增 42 個測試案例**，橫跨 3 個模組
- **覆蓋率提升** 從 83% 增加到 84%
- **100% 測試透過率** (總計 391 個測試)

**詳情**:

- `batch_processor`: 71% → 74% (+16 個測試)
- `result_parser`: 75% → 91% (+18 個測試)  
- `streaming_utils`: 67% → 85% (+8 個測試)

#### 📚 完整檔案 (第 2 週)

新增 7 份全面指南：

- 快速開始指南 - 5 分鐘內上手
- API 參考 - 完整的 API 檔案
- 最佳實踐 - 生產環境部署指南
- FAQ - 解答 40 多個常見問題
- 故障排除 - 調查與修復問題
- 架構設計 - 系統設計圖解
- 影片劇本 - 教學規劃

#### 🛠️ 範例工具

新增 5 個實用的範例工具：

1. **收據掃描器** - 提取發票資訊
2. **效能基準測試** - 測試與最佳化效能
3. **名片掃描器** - 提取聯絡人並匯出 vCard
4. **CLI 美化器** - Rich 終端機 UI
5. **檔案分類器** - 自動分類檔案型別

#### 🚀 DevOps 與 CI/CD

生產級基礎設施：

- **GitHub Actions** - 自動化測試與部署
- **Docker 支援** - 多階段建置配置
- **PyPI 準備** - 用於分發的 setup.py
- **Issue 範本** - Bug 回報與功能建議
- **貢獻指南** - 開源準備就緒

---

## 📦 安裝

```bash
pip install paddleocr-toolkit
```

或是從原始碼安裝：

```bash
git clone https://github.com/danwin47-sys/paddleocr-toolkit.git
cd paddleocr-toolkit
pip install -e .
```

---

## 🔧 重大變更

無 - 完全向下相容於 v1.0.0

---

## 🐛 Bug 修復

- 修復端對端 (e2e) 測試失敗問題
- 改善 Windows 編碼相容性
- 增強串流工具 (streaming utils) 中的錯誤處理

---

## ⚡ 效能

- 維持 v1.0.0 的優異效能
- 記憶體使用：處理大型 PDF 時 < 400MB
- 速度：平均每頁 1.25 秒

---

## 📊 資料統計

```
總測試數:         391 (較 v1.0.0 增加 45 個)
測試覆蓋率:       84% (+1%)
模組數:           26 (+7)
範例工具:         5 (新增)
檔案檔案:         13 個 (新增)
```

---

## 🤝 貢獻者

- 開發: Antigravity AI
- 測試: 社群
- 檔案: 已完成

---

## 📖 檔案

- [快速開始](docs/QUICK_START.md)
- [API 指南](docs/API_GUIDE.md)
- [最佳實踐](docs/BEST_PRACTICES.md)
- [範例](examples/)
- [貢獻指南](CONTRIBUTING.md)

---

## 🔗 連結

- [GitHub 儲存庫](https://github.com/danwin47-sys/paddleocr-toolkit)
- [Issue 追蹤器](https://github.com/danwin47-sys/paddleocr-toolkit/issues)
- [更新日誌](CHANGELOG.md)

---

## 🙏 致謝

- PaddleOCR 團隊提供優異的 OCR 引擎  
- 貢獻者與使用者的回饋
- 開源社群

---

**完整更新日誌**: [v1.0.0...v1.1.0](https://github.com/danwin47-sys/paddleocr-toolkit/compare/v1.0.0...v1.1.0)
