#!/bin/bash

# 快速測試腳本 - 只執行關鍵檢查

set -e

echo "⚡ 快速測試模式..."
echo ""

# Python 語法檢查
echo "🐍 Python 語法檢查..."
python -m py_compile paddleocr_toolkit/api/main.py
echo "✓ 通過"

# 前端 TypeScript 檢查（僅類型檢查，不build）
echo ""
echo "📝 TypeScript 類型檢查..."
cd web-frontend
npx tsc --noEmit
echo "✓ 通過"
cd ..

echo ""
echo "✅ 快速測試完成！"
