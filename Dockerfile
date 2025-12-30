# 使用輕量級 Python 3.10 映像檔
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    # 禁用 PaddlePaddle 的模型下載檢查 (我們會預先下載或在運行時處理)
    DISABLE_MODEL_SOURCE_CHECK=1

# 安裝系統依賴 (OpenCV 和 PaddlePaddle 所需)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
# 注意：paddlepaddle 和 paddleocr 可能需要較長時間編譯或下載
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式程式碼
COPY . .

# 建立必要的目錄
RUN mkdir -p uploads outputs paddleocr_toolkit/plugins

# 暴露端口 (Cloud Run 預設為 8080)
EXPOSE 8080

# 啟動命令
# 使用 uvicorn 啟動 FastAPI，監聽 0.0.0.0 和環境變數 PORT
CMD exec uvicorn paddleocr_toolkit.api.main:app --host 0.0.0.0 --port ${PORT}
