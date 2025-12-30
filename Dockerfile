# Stage 1: Builder
FROM python:3.10-slim as builder

WORKDIR /app

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 安裝構建依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 依賴
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.10-slim

WORKDIR /app

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH"

# 安裝 Runtime 系統依賴 (OpenCV 需求)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 從 Builder 複製 Python 套件
COPY --from=builder /root/.local /root/.local

# 複製專案代碼
COPY . .

# 建立所需目錄
RUN mkdir -p uploads output logs

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["uvicorn", "paddleocr_toolkit.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
