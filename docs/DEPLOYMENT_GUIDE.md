# PaddleOCR Toolkit 生產環境部署指南

**版本**：v3.6.0  
**更新日期**：2026-01-01

---

## 📋 目錄

- [部署架構](#部署架構)
- [方案選擇](#方案選擇)
- [Docker 部署](#docker-部署)
- [Vercel + Railway 部署](#vercel--railway-部署)
- [環境變數配置](#環境變數配置)
- [部署檢查清單](#部署檢查清單)
- [監控與維護](#監控與維護)

---

## 部署架構

### 系統組成
```
┌─────────────────┐
│   使用者瀏覽器   │
└────────┬────────┘
         │ HTTPS
         ↓
┌─────────────────┐      ┌──────────────────┐
│  前端 (Next.js)  │─────→│  後端 (FastAPI)  │
│   Vercel/CDN    │ API  │  Railway/Docker  │
└─────────────────┘      └──────────┬───────┘
                                    │
                         ┌──────────┴──────────┐
                         │  PaddleOCR 模型     │
                         │  (本地載入)         │
                         └─────────────────────┘
```

---

## 方案選擇

### 方案 A：Docker + Cloud Run ⭐ 推薦（中大型使用）

**優點**：
- 自動擴展
- 按使用量付費
- 隔離性好
- 易於維護

**適合**：
- 預期使用者 > 100
- 需要高可用性
- 願意支付雲端費用

**預算**：$20-50/月

---

### 方案 B：Vercel + Railway ⭐⭐ 推薦（小型使用）

**優點**：
- 前端免費
- 後端有免費額度
- Git 自動部署
- 設置簡單

**適合**：
- 個人或小團隊
- 預期使用者 < 50
- 預算有限

**預算**：$0-10/月

---

### 方案 C：本地 + ngrok（測試用）

**優點**：
- 無需雲端費用
- 快速測試
- 完全控制

**適合**：
- 臨時展示
- 內部測試
- 開發階段

**預算**：$0（ngrok 免費版）

---

## Docker 部署

### 1. 建立 Dockerfile

**後端 Dockerfile**：
```dockerfile
# paddleocr-toolkit/Dockerfile
FROM python:3.9-slim

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 設定工作目錄
WORKDIR /app

# 複製需求檔案
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案檔案
COPY . .

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["uvicorn", "paddleocr_toolkit.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**前端 Dockerfile**：
```dockerfile
# web-frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# 複製 package.json
COPY package*.json ./

# 安裝依賴
RUN npm ci

# 複製專案檔案
COPY . .

# 建立生產版本
RUN npm run build

# 生產環境
FROM node:18-alpine

WORKDIR /app

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["npm", "start"]
```

### 2. docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV=production
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
    restart: unless-stopped

  frontend:
    build: ./web-frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
      - NEXT_PUBLIC_GA_ID=${GA_ID}
    depends_on:
      - backend
    restart: unless-stopped
```

### 3. 部署到 Google Cloud Run

```bash
# 1. 安裝 gcloud CLI
# https://cloud.google.com/sdk/docs/install

# 2. 登入
gcloud auth login

# 3. 設定專案
gcloud config set project YOUR_PROJECT_ID

# 4. 建立並推送 Docker 映像
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/paddleocr-backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/paddleocr-frontend ./web-frontend

# 5. 部署後端
gcloud run deploy paddleocr-backend \
  --image gcr.io/YOUR_PROJECT_ID/paddleocr-backend \
  --platform managed \
  --region asia-east1 \
  --memory 2Gi \
  --timeout 300 \
  --allow-unauthenticated

# 6. 部署前端
gcloud run deploy paddleocr-frontend \
  --image gcr.io/YOUR_PROJECT_ID/paddleocr-frontend \
  --platform managed \
  --region asia-east1 \
  --set-env-vars NEXT_PUBLIC_API_URL=https://your-backend-url \
  --allow-unauthenticated
```

---

## Vercel + Railway 部署

### 方案架構
- **前端**：Vercel（免費，全球 CDN）
- **後端**：Railway（$5/月，500MB RAM）

### 1. 前端部署到 Vercel

#### A. 準備工作
```bash
# 確保專案在 Git 倉庫
git add .
git commit -m "準備部署"
git push origin main
```

#### B. Vercel 部署步驟

1. **登入 Vercel**
   - 前往 https://vercel.com
   - 使用 GitHub 帳號登入

2. **導入專案**
   - 點擊 "New Project"
   - 選擇您的 GitHub 倉庫
   - Root Directory: `web-frontend`

3. **配置環境變數**
   ```
   NEXT_PUBLIC_API_URL=https://your-railway-backend-url
   NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
   ```

4. **部署**
   - 點擊 "Deploy"
   - 等待建置完成
   - 獲得前端 URL：`https://your-app.vercel.app`

### 2. 後端部署到 Railway

#### A. 準備 railway.json

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn paddleocr_toolkit.api.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### B. Railway 部署步驟

1. **登入 Railway**
   - 前往 https://railway.app
   - 使用 GitHub 帳號登入

2. **新建專案**
   - 點擊 "New Project"
   - 選擇 "Deploy from GitHub repo"
   - 選擇您的倉庫

3. **配置環境變數**
   ```
   PORT=8000
   PYTHONUNBUFFERED=1
   ```

4. **設定根目錄**
   - Settings → Root Directory: `/`

5. **生成域名**
   - Settings → Generate Domain
   - 獲得後端 URL：`https://your-app.railway.app`

6. **更新 Vercel 環境變數**
   - 回到 Vercel
   - Settings → Environment Variables
   - 更新 `NEXT_PUBLIC_API_URL` 為 Railway URL
   - 重新部署前端

---

## 環境變數配置

### 前端環境變數

**檔案**：`web-frontend/.env.production`

```bash
# API 端點
NEXT_PUBLIC_API_URL=https://your-backend-url

# Google Analytics
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX

# 其他配置
NEXT_PUBLIC_ENV=production
```

### 後端環境變數

**設定在雲端平台**：

```bash
# 基本配置
ENV=production
PORT=8000

# API Keys（可選）
GEMINI_API_KEY=your_gemini_key
CLAUDE_API_KEY=your_claude_key

# CORS 設定
ALLOWED_ORIGINS=https://your-frontend-url
```

---

## 部署檢查清單

### 部署前檢查
- [ ] 所有功能本地測試通過
- [ ] 環境變數已配置
- [ ] Git 倉庫已推送
- [ ] 生產環境配置已就緒
- [ ] 備份重要資料

### 部署時檢查
- [ ] Docker 映像建置成功
- [ ] 環境變數正確設定
- [ ] CORS 設定正確
- [ ] 域名指向正確

### 部署後檢查
- [ ] 前端可正常訪問
- [ ] 後端 API 可正常調用
- [ ] 檔案上傳功能正常
- [ ] OCR 處理功能正常
- [ ] 可搜尋 PDF 功能正常
- [ ] 批量處理功能正常
- [ ] 錯誤處理正確
- [ ] 效能符合預期

---

## SSL 憑證

### Vercel 和 Railway
- **自動提供 SSL**
- 無需額外配置
- Let's Encrypt 免費憑證

### 自建伺服器
```bash
# 使用 Certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 監控與維護

### 1. 日誌監控

**Railway 日誌**：
```bash
# 在 Railway 控制台查看即時日誌
# 或使用 Railway CLI
railway logs
```

**Vercel 日誌**：
- 在 Vercel Dashboard 查看
- Functions → Logs

### 2. 效能監控

**建議工具**：
- Google Analytics（已整合）
- Sentry（錯誤追蹤）
- Uptime Robot（可用性監控）

**Sentry 整合**：
```bash
# 安裝
npm install @sentry/nextjs  # 前端
pip install sentry-sdk        # 後端

# 配置
# 參考 https://docs.sentry.io
```

### 3. 定期維護

**每週**：
- 檢查日誌是否有錯誤
- 監控使用量

**每月**：
- 更新依賴套件
- 檢查安全漏洞
- 清理舊資料

**每季**：
- 效能優化
- 功能更新
- 使用者反饋整合

---

## 故障排除

### 常見問題

#### 1. CORS 錯誤
**症狀**：前端無法調用後端 API

**解決**：
```python
# paddleocr_toolkit/api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-url"],  # 更新為實際 URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 2. 記憶體不足
**症狀**：處理大檔案時崩潰

**解決**：
- Railway：升級到更大的方案
- Cloud Run：增加記憶體限制（--memory 4Gi）

#### 3. 模型載入失敗
**症狀**：首次請求超時

**解決**：
- 增加超時設定
- 使用模型預載（已實作）

---

## 成本估算

### Vercel + Railway（小型）
| 項目         | 費用      |
| ------------ | --------- |
| Vercel 前端  | $0        |
| Railway 後端 | $5/月     |
| **總計**     | **$5/月** |

**適合**：< 50 使用者
**流量**：100GB/月

### Google Cloud Run（中型）
| 項目           | 費用       |
| -------------- | ---------- |
| Cloud Run 前端 | $10/月     |
| Cloud Run 後端 | $30/月     |
| **總計**       | **$40/月** |

**適合**：100-500 使用者
**流量**：無限制

---

## 安全建議

### 1. API 認證
```python
# 添加 API Key 驗證
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

@app.post("/api/ocr")
async def ocr(api_key: str = Security(API_KEY_HEADER)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    # ... 處理邏輯
```

### 2. 速率限制
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/ocr")
@limiter.limit("10/minute")
async def ocr():
    # ... 處理邏輯
```

### 3. 檔案大小限制
```python
@app.post("/api/ocr")
async def ocr(file: UploadFile = File(...)):
    MAX_SIZE = 50 * 1024 * 1024  # 50MB
    
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="檔案過大")
```

---

## 📝 總結

**推薦方案**：
- **小型使用**：Vercel + Railway（$5/月）
- **中大型使用**：Docker + Cloud Run（$40/月）

**關鍵步驟**：
1. 準備 Docker 或配置雲端平台
2. 設定環境變數
3. 部署前後端
4. 測試所有功能
5. 設定監控

**所需時間**：3-4 小時

---

**準備好部署了嗎？按照本指南操作即可！** 🚀
