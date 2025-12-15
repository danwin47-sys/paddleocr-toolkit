# Docker部署指南

PaddleOCR Toolkit Docker部署文檔。

---

## 🐳 快速開始

### 方法1：Docker Compose（推薦）

```bash
# 啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

訪問：

- Web界面: <http://localhost>
- API文檔: <http://localhost:8000/docs>

---

### 方法2：單獨Docker

```bash
# 建構映像
docker build -t paddleocr-toolkit .

# 執行容器
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/output:/app/output \
  --name paddleocr \
  paddleocr-toolkit
```

---

## 📦 服務組成

### API服務

- **連接埠**: 8000
- **映像**: 自行建構
- **卷**: uploads, output, logs

### Web服務

- **連接埠**: 80
- **映像**: nginx:alpine
- **功能**:
  - 提供Web界面
  - API反向代理
  - WebSocket代理

### Redis（可選）

- **連接埠**: 6379
- **用途**: 任務佇列和快取

---

## ⚙️ 設定

### 環境變數

在 `docker-compose.yml` 中設定：

```yaml
environment:
  - UPLOAD_DIR=/app/uploads
  - OUTPUT_DIR=/app/output
  - REDIS_URL=redis://redis:6379
  - MAX_WORKERS=4
```

---

### 卷掛載

```yaml
volumes:
  - ./uploads:/app/uploads    # 上傳檔案
  - ./output:/app/output      # 輸出結果
  - ./logs:/app/logs          # 日誌檔案
```

---

## 🚀 GPU支援

### 啟用GPU

在 `docker-compose.yml` 中取消註釋：

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

### 需求

1. 安裝 NVIDIA Docker Runtime：

   ```bash
   # Ubuntu
   sudo apt-get install nvidia-docker2
   sudo systemctl restart docker
   ```

2. 驗證：

   ```bash
   docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
   ```

---

## 📊 監控

### 查看日誌

```bash
# 所有服務
docker-compose logs -f

# 特定服務
docker-compose logs -f api
docker-compose logs -f web
```

### 服務狀態

```bash
# 查看執行中的容器
docker-compose ps

# 資源使用
docker stats
```

---

## 🔧 維護

### 更新映像

```bash
# 重新建構
docker-compose build

# 重新啟動
docker-compose up -d --build
```

### 備份資料

```bash
# 備份上傳和輸出
tar -czf backup.tar.gz uploads/ output/
```

### 清理空間

```bash
# 清理舊檔案（透過API）
curl -X POST http://localhost:8000/api/files/cleanup?days=7

# 清理Docker
docker system prune -a
```

---

## 🌐 生產環境部署

### 1. 使用環境變數檔

建立 `.env` 檔案：

```env
API_HOST=0.0.0.0
API_PORT=8000
MAX_WORKERS=8
UPLOAD_LIMIT=100M
REDIS_URL=redis://redis:6379
```

### 2. 啟用HTTPS

更新 `nginx.conf`：

```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    # ... 其他設定
}
```

### 3. 設定重啟策略

```yaml
restart: always
```

### 4. 資源限制

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

---

## 🐛 疑難排解

### API無法啟動

檢查日誌：

```bash
docker-compose logs api
```

常見問題：

- 連接埠衝突：修改 `docker-compose.yml` 中的連接埠
- 權限問題：確保卷目錄可寫

### Web界面無法訪問

1. 檢查nginx狀態：

   ```bash
   docker-compose logs web
   ```

2. 驗證API連線：

   ```bash
   curl http://localhost:8000/
   ```

### GPU不可用

1. 檢查NVIDIA驅動：

   ```bash
   nvidia-smi
   ```

2. 驗證Docker GPU支援：

   ```bash
   docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
   ```

---

## 📝 常用命令

```bash
# 啟動
docker-compose up -d

# 停止
docker-compose down

# 重啟
docker-compose restart

# 查看日誌
docker-compose logs -f

# 進入容器
docker-compose exec api bash

# 更新並重啟
docker-compose up -d --build

# 僅啟動API
docker-compose up -d api

# 擴展服務
docker-compose up -d --scale api=3
```

---

**更多資訊**: [Docker官方文檔](https://docs.docker.com/)
