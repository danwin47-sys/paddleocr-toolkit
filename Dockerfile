# 使用 Python 3.10 作為基礎映像
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# 安裝系統依賴
# libgl1-mesa-glx 和 libglib2.0-0 是 OpenCV 所需
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
# 使用清華鏡像加速下載 (可選)
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案代碼
COPY . .

# 建立上傳目錄
RUN mkdir -p uploads

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["uvicorn", "paddleocr_toolkit.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
