# Multi-stage build for production
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 ocr && \
    mkdir -p /app /data && \
    chown -R ocr:ocr /app /data

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/ocr/.local

# Make sure scripts are in PATH
ENV PATH=/home/ocr/.local/bin:$PATH

# Copy application
COPY --chown=ocr:ocr . .

# Switch to non-root user
USER ocr

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DISABLE_MODEL_SOURCE_CHECK=True

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "from paddle_ocr_tool import PaddleOCRTool; print('OK')" || exit 1

# Expose port (if running as API)
EXPOSE 8000

# Default command
CMD ["python", "paddle_ocr_tool.py", "--help"]
