
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "      PaddleOCR Toolkit - Local CI/CD Runner (v3.3.0)   " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"
$global:LASTEXITCODE = 0

function Run-Step {
    param (
        [string]$Name,
        [scriptblock]$Command,
        [switch]$AllowFail
    )
    Write-Host "`n[Running] $Name..." -ForegroundColor Yellow
    try {
        & $Command
        if ($LASTEXITCODE -ne 0) {
            if ($AllowFail) {
                Write-Host "[Warning] $Name failed (Exit code $LASTEXITCODE), but continuing..." -ForegroundColor DarkYellow
                return
            }
            throw "Command failed with exit code $LASTEXITCODE"
        }
        Write-Host "[Success] $Name" -ForegroundColor Green
    }
    catch {
        if ($AllowFail) {
            Write-Host "[Warning] $Name failed, but continuing..." -ForegroundColor DarkYellow
        }
        else {
            Write-Host "[Failed] $Name" -ForegroundColor Red
            Write-Host $_ -ForegroundColor Red
            exit 1
        }
    }
}

# 1. Dependency Check
Run-Step "Dependency Check" {
    # 簡單檢查關鍵開發工具是否存在
    foreach ($tool in @("black", "isort", "flake8", "mypy", "pytest", "twine")) {
        if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
            Write-Host "Installing missing dev dependencies..." -ForegroundColor Yellow
            pip install --no-cache-dir -r requirements-ci.txt
            break
        }
    }
}

# 2. Formatting (Auto-fix)
Run-Step "Code Formatting (Black + Isort)" {
    $paths = "paddleocr_toolkit/", "tests/", "plugins/", "examples/", "scripts/", "setup.py", "paddle_ocr_tool.py", "pdf_translator.py"
    # 自動修復
    black $paths
    isort --profile black $paths
}

# 3. Linting
Run-Step "Linting (Flake8)" {
    # 與 GitHub Actions 設定一致 (.github/workflows/ci.yml)
    flake8 paddleocr_toolkit/ --max-line-length=120 --ignore="E203,W503,F401,E722,W293,F841,E741,F541,W291,E226,E402" --exclude="__pycache__,.git,.mypy_cache"
}

# 4. Type Checking
Run-Step "Type Checking (Mypy)" {
    # 忽略 missing imports 因為某些依賴可能沒裝完整型別
    # CI 設定為 || true，所以允許失敗
    mypy paddleocr_toolkit/ --ignore-missing-imports
} -AllowFail

# 5. Testing
Run-Step "Unit Tests (Pytest)" {
    pytest tests/ --cov=paddleocr_toolkit --cov-report=term
}

# 6. Building
Run-Step "Package Build" {
    if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
    python -m build
    twine check dist/*
}

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host "      🎉 All CI/CD Steps Passed Successfully!           " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
