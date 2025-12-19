# Docker 部署指南

## 快速開始

### 1. 環境準備

```bash
# 複製環境變數範本
cp .env.example .env

# 編輯 .env 設定 API Key
nano .env
```

### 2. 啟動服務

```bash
# 啟動所有服務
docker-compose up -d

# 檢視日誌
docker-compose logs -f
```

### 3. 初始化 Ollama 模型

```bash
# 進入 Ollama 容器
docker exec -it paddleocr-ollama bash

# 下載模型（首次使用）
ollama pull qwen2.5:7b

# 退出容器
exit
```

### 4. 測試 API

```bash
# 健康檢查
curl http://localhost:8000/docs

# 測試 OCR（需要 API Key）
curl -X POST http://localhost:8000/api/ocr \
  -H "X-API-Key: your-api-key-here" \
  -F "file=@test.pdf"
```

## 服務說明

### Ollama (LLM 服務)
- **埠**: 11434
- **用途**: 提供本地 LLM 推理
- **資料持久化**: `ollama_data` volume

### PaddleOCR API
- **埠**: 8000
- **API 文件**: http://localhost:8000/docs
- **上傳目錄**: `./uploads`
- **輸出目錄**: `./output`

## 環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `API_KEY` | dev-key-change-in-production | API 認證金鑰 |
| `ALLOWED_ORIGINS` | * | CORS 允許的來源 |
| `OLLAMA_MODEL` | qwen2.5:7b | Ollama 模型名稱 |
| `ENABLE_PLUGINS` | true | 是否啟用外掛 |

## 生產環境部署

### 安全性設定

1. **設定強 API Key**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))" > api_key.txt
# 將生成的 key 設定到 .env
```

2. **限制 CORS**:
```env
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

3. **禁用外掛**（如不需要）:
```env
ENABLE_PLUGINS=false
```

### 使用 HTTPS

建議使用 Nginx 或 Traefik 作為反向代理：

```nginx
server {
    listen 443 ssl;
    server_name ocr.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 維護

### 檢視日誌
```bash
# 所有服務
docker-compose logs -f

# 特定服務
docker-compose logs -f paddleocr-api
docker-compose logs -f ollama
```

### 重啟服務
```bash
# 重啟所有服務
docker-compose restart

# 重啟特定服務
docker-compose restart paddleocr-api
```

### 更新服務
```bash
# 拉取最新程式碼
git pull

# 重新建構並啟動
docker-compose up -d --build
```

### 清理
```bash
# 停止並移除容器
docker-compose down

# 同時移除 volumes（會刪除資料！）
docker-compose down -v
```

## 故障排除

### Ollama 無法連線
```bash
# 檢查 Ollama 健康狀態
docker exec paddleocr-ollama curl http://localhost:11434/api/tags

# 重啟 Ollama
docker-compose restart ollama
```

### API 無法啟動
```bash
# 檢視詳細日誌
docker-compose logs paddleocr-api

# 檢查環境變數
docker exec paddleocr-api env | grep -E "API_KEY|OLLAMA"
```

### 記憶體不足
```bash
# 限制容器記憶體
# 在 docker-compose.yml 中新增：
services:
  paddleocr-api:
    mem_limit: 4g
    memswap_limit: 4g
```

## 效能最佳化

### GPU 支援

如果有 NVIDIA GPU：

```yaml
services:
  paddleocr-api:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - PADDLEOCR_DEVICE=gpu
```

### 擴充套件服務

```bash
# 執行多個 API 例項
docker-compose up -d --scale paddleocr-api=3
```

## 監控

### Prometheus + Grafana（可選）

參考 `monitoring/docker-compose.monitoring.yml` 配置。

## 支援

如遇問題，請檢視：
- [GitHub Issues](https://github.com/danwin47-sys/paddleocr-toolkit/issues)
- [安全性指南](docs/SECURITY_HARDENING.md)
- [API 文件](docs/FACADE_API_GUIDE.md)
