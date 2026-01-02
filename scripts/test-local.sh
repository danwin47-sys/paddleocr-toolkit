#!/bin/bash

# 本地 CI/CD 測試腳本
# 在提交前執行，確保代碼品質

set -e  # 遇到錯誤立即退出

# 解析命令行參數
RUN_PYTEST=false
for arg in "$@"; do
    if [ "$arg" = "--with-pytest" ] || [ "$arg" = "-p" ]; then
        RUN_PYTEST=true
    fi
done

echo "🚀 開始本地 CI/CD 測試..."
if [ "$RUN_PYTEST" = true ]; then
    echo "📊 pytest 單元測試：已啟用"
fi
echo ""

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 測試結果追蹤
TESTS_PASSED=0
TESTS_FAILED=0

# ==================== 1. Python 後端測試 ====================
echo "📦 [1/5] 檢查 Python 後端..."

# 1.1 檢查 Python 語法
echo "  → 檢查 Python 語法..."
if python -m py_compile paddleocr_toolkit/api/main.py paddleocr_toolkit/core/ocr_engine.py; then
    echo -e "  ${GREEN}✓${NC} Python 語法檢查通過"
    ((TESTS_PASSED++))
else
    echo -e "  ${RED}✗${NC} Python 語法錯誤"
    ((TESTS_FAILED++))
fi

# 1.2 檢查 Python import
echo "  → 檢查 Python imports..."
if python -c "
import sys
sys.path.insert(0, '.')
try:
    from paddleocr_toolkit.api import main
    from paddleocr_toolkit.core import ocr_engine
    print('Imports OK')
except Exception as e:
    print(f'Import error: {e}')
    sys.exit(1)
" 2>&1 | grep -v "INTEL MKL"; then
    echo -e "  ${GREEN}✓${NC} Python imports 正常"
    ((TESTS_PASSED++))
else
    echo -e "  ${RED}✗${NC} Python imports 失敗"
    ((TESTS_FAILED++))
fi

# 1.3 檢查 Python 單元測試 (可選)
if [ "$RUN_PYTEST" = true ]; then
    echo "  → 執行 pytest 單元測試..."
    if command -v pytest &> /dev/null; then
        if pytest tests/ -v --tb=short 2>&1 | tee /tmp/pytest_output.txt | tail -20; then
            echo -e "  ${GREEN}✓${NC} pytest 測試通過"
            ((TESTS_PASSED++))
        else
            echo -e "  ${RED}✗${NC} pytest 測試失敗"
            ((TESTS_FAILED++))
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} pytest 未安裝，跳過測試"
        echo "  提示：安裝 pytest: pip install pytest pytest-cov"
    fi
fi

# ==================== 2. 前端測試 ====================
echo ""
echo "🎨 [2/5] 檢查前端代碼..."

cd web-frontend

# 2.1 TypeScript 編譯檢查
echo "  → TypeScript 編譯檢查..."
if npm run build > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} TypeScript 編譯成功"
    ((TESTS_PASSED++))
else
    echo -e "  ${YELLOW}⚠${NC} TypeScript 編譯警告（檢查 .next/build.log）"
fi

# 2.2 ESLint 檢查
echo "  → ESLint 代碼檢查..."
if npm run lint > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} ESLint 檢查通過"
    ((TESTS_PASSED++))
else
    echo -e "  ${YELLOW}⚠${NC} ESLint 有警告"
fi

cd ..

# ==================== 3. Git 狀態檢查 ====================
echo ""
echo "📝 [3/5] 檢查 Git 狀態..."

# 3.1 檢查是否有未追蹤的大檔案
echo "  → 檢查大檔案..."
LARGE_FILES=$(find . -type f -size +10M -not -path "./.git/*" -not -path "./web-frontend/node_modules/*" -not -path "./web-frontend/.next/*" 2>/dev/null)
if [ -z "$LARGE_FILES" ]; then
    echo -e "  ${GREEN}✓${NC} 無大檔案（>10MB）"
    ((TESTS_PASSED++))
else
    echo -e "  ${YELLOW}⚠${NC} 發現大檔案:"
    echo "$LARGE_FILES"
fi

# 3.2 檢查敏感資訊
echo "  →檢查敏感資訊..."
SECRETS_FOUND=0
# 排除測試檔案和特定目錄，並只檢查實際的 key 賦值（排除類型提示和參數定義）
# 匹配 api_key = "actual_key_string" 但不匹配 api_key: str 或 api_key 參數
if grep -rE "api_key\s*=\s*['\"][a-zA-Z0-9_-]{20,}['\"]" \
    --include="*.py" --include="*.ts" --include="*.tsx" \
    --exclude-dir="node_modules" \
    --exclude-dir=".git" \
    --exclude-dir="tests" \
    --exclude-dir="__pycache__" \
    --exclude-dir=".pytest_cache" \
    . 2>/dev/null; then
    echo -e "  ${RED}✗${NC} 發現可能的真實 API key！"
    echo -e "  ${YELLOW}提示：${NC} 請使用環境變數而非硬編碼"
    ((TESTS_FAILED++))
    SECRETS_FOUND=1
fi

if [ $SECRETS_FOUND -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} 未發現明文 API key"
    ((TESTS_PASSED++))
fi

# ==================== 4. 依賴檢查 ====================
echo ""
echo "📚 [4/5] 檢查依賴..."

# 4.1 Python 依賴
echo "  → 檢查 Python 依賴..."
if [ -f "requirements.txt" ]; then
    echo -e "  ${GREEN}✓${NC} requirements.txt 存在"
    ((TESTS_PASSED++))
else
    echo -e "  ${RED}✗${NC} requirements.txt 不存在"
    ((TESTS_FAILED++))
fi

# 4.2 Node 依賴
echo "  → 檢查 Node.js 依賴..."
if [ -f "web-frontend/package.json" ]; then
    echo -e "  ${GREEN}✓${NC} package.json 存在"
    ((TESTS_PASSED++))
else
    echo -e "  ${RED}✗${NC} package.json 不存在"
    ((TESTS_FAILED++))
fi

# ==================== 5. 文檔檢查 ====================
echo ""
echo "📖 [5/5] 檢查文檔..."

# 5.1 README 存在性
if [ -f "README.md" ]; then
    echo -e "  ${GREEN}✓${NC} README.md 存在"
    ((TESTS_PASSED++))
else
    echo -e "  ${YELLOW}⚠${NC} README.md 不存在"
fi

# 5.2 CHANGELOG 更新
if [ -f "CHANGELOG.md" ]; then
    echo -e "  ${GREEN}✓${NC} CHANGELOG.md 存在"
    ((TESTS_PASSED++))
else
    echo -e "  ${YELLOW}⚠${NC} CHANGELOG.md 不存在"
fi

# ==================== 總結 ====================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 測試結果總結"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "通過: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "失敗: ${RED}${TESTS_FAILED}${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 所有測試通過！可以安全提交。${NC}"
    exit 0
else
    echo -e "${RED}❌ 有 ${TESTS_FAILED} 項測試失敗，請修復後再提交。${NC}"
    exit 1
fi
