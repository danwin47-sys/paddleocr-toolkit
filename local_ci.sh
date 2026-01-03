#!/bin/bash
set -e

# local_ci.sh - Entry point for Local CI/CD pipeline

echo "=================================================="
echo "🔧 Setting up Local CI/CD Environment"
echo "=================================================="

# 1. Install/Update Python Dependencies
echo "📦 Installing/Updating Python dependencies (CI profile)..."
# Upgrade pip to ensure wheel resolution works
python -m pip install --upgrade pip
# Use requirements-ci.txt to avoid paddlepaddle installation issues on local environment
# and to match CI environment.
python -m pip install -r requirements-ci.txt
echo "✅ Dependencies updated."
echo ""

# 2. Run the Test Suite (Delegating to scripts/test-local.sh)
echo "🚀 Launching Test Suite..."
# Ensure script is executable
chmod +x scripts/test-local.sh
./scripts/test-local.sh "$@"
