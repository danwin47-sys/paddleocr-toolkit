"""
簡單的自動化測試
用於快速驗證核心功能
"""

import pytest
from pathlib import Path


def test_project_structure():
    """測試專案結構完整性"""
    # 檢查主要目錄
    assert Path("paddleocr_toolkit").exists()
    assert Path("web-frontend").exists()
    assert Path("scripts").exists()
    assert Path("docs").exists()

    # 檢查關鍵檔案
    assert Path("README.md").exists()
    assert Path("requirements.txt").exists()
    assert Path("CHANGELOG.md").exists()


def test_scripts_executable():
    """測試腳本可執行性"""
    scripts = [
        Path("scripts/test-local.sh"),
        Path("scripts/test-quick.sh"),
        Path("scripts/install-hooks.sh"),
    ]

    for script in scripts:
        assert script.exists(), f"{script} 不存在"
        # 檢查執行權限
        assert script.stat().st_mode & 0o111, f"{script} 沒有執行權限"


def test_required_dependencies():
    """測試必要依賴存在"""
    requirements = Path("requirements.txt").read_text()

    essential_deps = [
        "fastapi",
        "uvicorn",
        "PyMuPDF",
        "reportlab",
    ]

    for dep in essential_deps:
        assert dep.lower() in requirements.lower(), f"缺少依賴：{dep}"


def test_frontend_structure():
    """測試前端結構"""
    frontend_path = Path("web-frontend")

    # 檢查配置檔案
    assert (frontend_path / "package.json").exists()
    assert (frontend_path / "tsconfig.json").exists()

    # 檢查源碼目錄
    assert (frontend_path / "src").exists()
    assert (frontend_path / "src" / "app").exists()
    assert (frontend_path / "src" / "components").exists()


def test_api_structure():
    """測試 API 結構"""
    api_path = Path("paddleocr_toolkit/api")

    assert api_path.exists()
    assert (api_path / "main.py").exists()


def test_documentation():
    """測試文檔存在"""
    docs = [
        "docs/USER_GUIDE.md",
        "docs/DEPLOYMENT_GUIDE.md",
        "docs/FAQ.md",
    ]

    for doc in docs:
        assert Path(doc).exists(), f"文檔不存在：{doc}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
