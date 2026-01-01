#!/bin/bash

# 安裝 Git Hooks 腳本

echo "📦 安裝 CI/CD 環境..."
echo ""

# 1. 設置執行權限
echo "1. 設置腳本執行權限..."
chmod +x scripts/test-local.sh
chmod +x scripts/test-quick.sh
echo "  ✓ 完成"

# 2. 創建 pre-commit hook
echo ""
echo "2. 安裝 Git pre-commit hook..."
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

# Git Pre-commit Hook
# 在 commit 前自動執行測試

echo "🔍 執行 pre-commit 檢查..."

# 執行測試腳本
./scripts/test-local.sh

# 獲取測試結果
TEST_RESULT=$?

if [ $TEST_RESULT -ne 0 ]; then
    echo ""
    echo "❌ Pre-commit 檢查失敗！"
    echo "請修復錯誤後再提交，或使用 git commit --no-verify 跳過檢查"
    exit 1
fi

echo ""
echo "✅ Pre-commit 檢查通過！繼續提交..."
exit 0
EOF

chmod +x .git/hooks/pre-commit
echo "  ✓ Pre-commit hook 已安裝"

# 3. 測試 Hook
echo ""
echo "3. 測試 hook 是否正常..."
if [ -x .git/hooks/pre-commit ]; then
    echo "  ✓ Hook 可執行"
else
    echo "  ✗ Hook 無法執行"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ CI/CD 環境安裝完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 使用方式："
echo ""
echo "  完整測試：  ./scripts/test-local.sh"
echo "  快速測試：  ./scripts/test-quick.sh"
echo "  Git 提交：  git commit（自動執行測試）"
echo "  跳過檢查：  git commit --no-verify"
echo ""
echo "🎯 現在每次 commit 前都會自動執行測試！"
