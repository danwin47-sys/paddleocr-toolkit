# 使用輕量級 Python 3.10 映像檔
# 使用穩定的 Debian Bookworm 版本，並確保使用國內鏡像或穩定源 (如果需要)
FROM python:3.10-slim-bookworm

# 設定工作目錄
WORKDIR /app

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    # 限制並行工作數，避免記憶體溢出 (Render Free Tier 512MB RAM)
    OCR_WORKERS=1 \
    # 禁用 PaddlePaddle 的模型下載檢查 (我們會預先下載或在運行時處理)
    DISABLE_MODEL_SOURCE_CHECK=1

# 安裝系統依賴 (OpenCV Headless 和 PaddlePaddle 所需 - 移除 GUI 庫)
# 使用 --fix-missing 嘗試修復潛在的網絡問題
RUN apt-get update --fix-missing && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
# 注意：paddlepaddle 和 paddleocr 可能需要較長時間編譯或下載
RUN pip install --no-cache-dir -r requirements.txt

# 🚀 預載模型到 Docker Image (減少啟動時間和運行時記憶體)
# 先複製預載腳本
COPY preload_models.py .

# 暫時取消 DISABLE_MODEL_SOURCE_CHECK 以允許下載
ENV DISABLE_MODEL_SOURCE_CHECK=0

# 執行模型預載 (這會下載約 200MB 的模型檔案到 /root/.paddlex/)
RUN python preload_models.py

# 恢復 DISABLE_MODEL_SOURCE_CHECK (運行時不再需要檢查)
ENV DISABLE_MODEL_SOURCE_CHECK=1

# 複製應用程式程式碼
COPY . .

# 建立必要的目錄
RUN mkdir -p uploads outputs paddleocr_toolkit/plugins

# 暴露端口 (Cloud Run 預設為 8080)
EXPOSE 8080

# 啟動命令
# 使用 uvicorn 啟動 FastAPI，監聽 0.0.0.0 和環境變數 PORT
CMD exec uvicorn paddleocr_toolkit.api.main:app --host 0.0.0.0 --port ${PORT}
