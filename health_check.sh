#!/bin/bash
# PaddleOCR Toolkit 完整健康檢查腳本

echo "============================================"
echo "  PaddleOCR Toolkit 系統健康檢查"
echo "============================================"
echo ""

# 計數器
SUCCESS=0
WARNINGS=0
ERRORS=0

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 服務狀態檢查
echo "[1/8] 服務狀態檢查..."
echo "----------------------------------------"

# 後端
if ps aux | grep -v grep | grep "uvicorn" > /dev/null; then
    echo -e "${GREEN}✅ Backend (uvicorn): 運行中${NC}"
    ps aux | grep -v grep | grep "uvicorn" | awk '{print "   PID:", $2, "MEM:", $4"%"}'
    ((SUCCESS++))
else
    echo -e "${RED}❌ Backend: 未運行${NC}"
    ((ERRORS++))
fi

# 前端
if ps aux | grep -v grep | grep "next dev" > /dev/null; then
    echo -e "${GREEN}✅ Frontend (Next.js): 運行中${NC}"
    ps aux | grep -v grep | grep "next dev" | head -1 | awk '{print "   PID:", $2}'
    ((SUCCESS++))
else
    echo -e "${RED}❌ Frontend: 未運行${NC}"
    ((ERRORS++))
fi

echo ""

# 2. 端口檢查
echo "[2/8] 端口監聽檢查..."
echo "----------------------------------------"

if lsof -i:8000 | grep LISTEN > /dev/null; then
    echo -e "${GREEN}✅ Port 8000: LISTEN${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}❌ Port 8000: 未監聽${NC}"
    ((ERRORS++))
fi

if lsof -i:3000 | grep LISTEN > /dev/null; then
    echo -e "${GREEN}✅ Port 3000: LISTEN${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}❌ Port 3000: 未監聽${NC}"
    ((ERRORS++))
fi

echo ""

# 3. API 健康測試
echo "[3/8] API 健康測試..."
echo "----------------------------------------"

# 後端 Health Check
HTTP_CODE=$(curl -o /dev/null -s -w "%{http_code}" http://localhost:8000/health 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Backend API: 正常 (HTTP $HTTP_CODE)${NC}"
    ((SUCCESS++))
elif [ "$HTTP_CODE" = "404" ]; then
    echo -e "${YELLOW}⚠️  Backend API: 端點不存在 (HTTP $HTTP_CODE)${NC}"
    ((WARNINGS++))
else
    echo -e "${RED}❌ Backend API: 異常 (HTTP $HTTP_CODE)${NC}"
    ((ERRORS++))
fi

# 前端測試
HTTP_CODE=$(curl -o /dev/null -s -w "%{http_code}" http://localhost:3000/ 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Frontend: 正常 (HTTP $HTTP_CODE)${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}❌ Frontend: 異常 (HTTP $HTTP_CODE)${NC}"
    ((ERRORS++))
fi

echo ""

# 4. 磁碟空間檢查
echo "[4/8] 磁碟空間檢查..."
echo "----------------------------------------"

DISK_USAGE=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✅ 磁碟使用率: ${DISK_USAGE}%${NC}"
    ((SUCCESS++))
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${YELLOW}⚠️  磁碟使用率: ${DISK_USAGE}% (接近上限)${NC}"
    ((WARNINGS++))
else
    echo -e "${RED}❌ 磁碟使用率: ${DISK_USAGE}% (過高)${NC}"
    ((ERRORS++))
fi

echo ""

# 5. 目錄檢查
echo "[5/8] 必要目錄檢查..."
echo "----------------------------------------"

DIRS=("uploads" "outputs" "logs" ".cache")
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ] && [ -w "$dir" ]; then
        echo -e "${GREEN}✅ $dir/: 存在且可寫${NC}"
        ((SUCCESS++))
    else
        echo -e "${RED}❌ $dir/: 不存在或無權限${NC}"
        ((ERRORS++))
    fi
done

echo ""

# 6. 快取與檔案大小
echo "[6/8] 快取與暫存檔檢查..."
echo "----------------------------------------"

if [ -d ".cache" ]; then
    CACHE_SIZE=$(du -sh .cache 2>/dev/null | awk '{print $1}')
    echo "   Cache 大小: $CACHE_SIZE"
fi

if [ -d "uploads" ]; then
    UPLOAD_COUNT=$(find uploads -type f 2>/dev/null | wc -l | tr -d ' ')
    echo "   上傳檔案數: $UPLOAD_COUNT"
fi

if [ -d "outputs" ]; then
    OUTPUT_COUNT=$(find outputs -type f 2>/dev/null | wc -l | tr -d ' ')
    echo "   輸出檔案數: $OUTPUT_COUNT"
fi

echo -e "${GREEN}✅ 檔案系統檢查完成${NC}"
((SUCCESS++))

echo ""

# 7. 錯誤日誌檢查
echo "[7/8] 近期錯誤日誌..."
echo "----------------------------------------"

if [ -f "logs/paddleocr.log" ]; then
    ERROR_COUNT=$(tail -100 logs/paddleocr.log | grep -c "ERROR" 2>/dev/null | tr -d '\n' || echo "0")
    if [ "$ERROR_COUNT" -eq 0 ]; then
        echo -e "${GREEN}✅ 無近期錯誤 (最近 100 行)${NC}"
        ((SUCCESS++))
    elif [ "$ERROR_COUNT" -lt 5 ]; then
        echo -e "${YELLOW}⚠️  發現 $ERROR_COUNT 個錯誤 (最近 100 行)${NC}"
        echo "   最近錯誤:"
        tail -100 logs/paddleocr.log | grep "ERROR" | tail -3
        ((WARNINGS++))
    else
        echo -e "${RED}❌ 發現 $ERROR_COUNT 個錯誤 (最近 100 行)${NC}"
        echo "   最近錯誤:"
        tail -100 logs/paddleocr.log | grep "ERROR" | tail -3
        ((ERRORS++))
    fi
else
    echo -e "${YELLOW}⚠️  日誌檔案不存在: logs/paddleocr.log${NC}"
    ((WARNINGS++))
fi

echo ""

# 8. Python 套件檢查
echo "[8/8] 關鍵套件版本..."
echo "----------------------------------------"

python3 -c "
import paddleocr
import fastapi
import PIL
print(f'PaddleOCR: {paddleocr.__version__}')
print(f'FastAPI: {fastapi.__version__}')
print(f'Pillow: {PIL.__version__}')
" 2>/dev/null || echo -e "${YELLOW}⚠️  無法取得套件版本${NC}"

echo ""

# 總結報告
echo "============================================"
echo "  檢查完成 - 總結報告"
echo "============================================"
echo -e "${GREEN}成功: $SUCCESS${NC}"
echo -e "${YELLOW}警告: $WARNINGS${NC}"
echo -e "${RED}錯誤: $ERRORS${NC}"
echo ""

if [ "$ERRORS" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    echo -e "${GREEN}✨ 系統狀態良好，可正常使用！${NC}"
    exit 0
elif [ "$ERRORS" -eq 0 ]; then
    echo -e "${YELLOW}⚡ 系統基本正常，但有些警告需要注意${NC}"
    exit 0
else
    echo -e "${RED}🚨 系統存在問題，請檢查上述錯誤${NC}"
    exit 1
fi
