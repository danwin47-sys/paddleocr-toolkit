# 🚀 PaddleOCR Toolkit 混合架構啟動指南

本指南將引導您如何啟動本地 OCR 後端，並透過 ngrok 與 Vercel 前端連線。

---

## 📋 準備工作 (僅需執行一次)

在第一次使用前，請確保您的電腦已安裝以下工具：

1.  **安裝 ngrok**:
    ```bash
    brew install ngrok/ngrok/ngrok
    ```
2.  **註冊並設定 ngrok Authtoken**:
    *   前往 [ngrok 官網](https://dashboard.ngrok.com/get-started/your-authtoken) 註冊免費帳號。
    *   在終端機執行：
        ```bash
        ngrok config add-authtoken <您的Token>
        ```

---

## 🏃‍♂️ 日常啟動步驟 (一鍵啟動)

每當您想要使用 OCR 服務時，請執行以下步驟：

1.  **開啟終端機** 並進入專案目錄：
    ```bash
    cd paddleocr-toolkit
    ```
2.  **執行啟動腳本**:
    ```bash
    ./scripts/start-backend.sh
    ```
3.  **獲取網址**:
    *   腳本執行成功後，會顯示一行藍色的文字：`Public URL: https://xxxx-xxxx.ngrok-free.app`
    *   **請複製這個網址**。

---

## ☁️ 更新 Vercel 前端設定

為了讓雲端的網頁能連到您的電腦，您需要更新 Vercel 的環境變數：

1.  登入 [Vercel Dashboard](https://vercel.com/dashboard)。
2.  選擇 **paddleocr-toolkit** 專案。
3.  進入 **Settings** > **Environment Variables**。
4.  找到 `NEXT_PUBLIC_API_URL`，將其值修改為剛才複製的 **ngrok 網址**。
5.  **重要**: 修改後，通常需要重新部署 (Redeploy) 或是等待幾分鐘讓變數生效。

---

## 🛠️ 排錯與維護 (Troubleshooting)

### 1. 網頁顯示「無內容」但在處理中？
這通常是因為瀏覽器快取了舊的失敗結果。
*   **清理後端快取**:
    ```bash
    rm -rf .cache/ocr_results/*
    ```
*   **清理瀏覽器快取**: 重新整理網頁，或開啟無痕視窗測試。

### 2. 想查看詳細日誌 (Logs)？
*   **後端日誌**: `tail -f uvicorn.log`
*   **通道日誌**: `tail -f ngrok.log`

### 3. 如何強制停止所有服務？
如果您想完全重頭開始，可以執行：
```bash
pkill -f uvicorn && pkill -f ngrok
```

---

## 📝 備註
*   由於使用的是 ngrok 免費版，每次重新啟動網址都會改變，因此需要手動去 Vercel 更新變數。
*   如果不想每次改網址，可以考慮 [ngrok 的付費方案](https://ngrok.com/pricing) 來鎖定固定網址。
