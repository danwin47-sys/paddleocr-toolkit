# -*- coding: utf-8 -*-
"""
SemanticProcessor 實際測試

直接測試 SemanticProcessor 的功能（不需要安裝 package）
"""

import sys
from pathlib import Path

# 加入專案根目錄到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from paddleocr_toolkit.processors.semantic_processor import SemanticProcessor


def test_basic_correction():
    """測試基本錯誤修正"""
    print("=" * 70)
    print("測試 1：OCR 錯誤修正")
    print("=" * 70)
    
    processor = SemanticProcessor(llm_provider="ollama", model="qwen2.5:7b")
    
    if not processor.is_enabled():
        print("❌ Ollama 服務未啟動")
        print("   請確保 Ollama 正在運行：ollama serve")
        print("   並且已下載模型：ollama pull qwen2.5:7b")
        return False
    
    print("✅ Ollama 服務已連接")
    
    # 測試文字（包含典型 OCR 錯誤）
    test_cases = [
        {
            "input": "這個文建包含銷多OCR銷別字",
            "expected_keywords": ["文件", "錯", "很多"]
        },
        {
            "input": "PaddleOCR工見包是―個強太的工其",
            "expected_keywords": ["工具包", "一個", "強大", "工具"]
        },
        {
            "input": "請住意檢査錯沒",
            "expected_keywords": ["注意", "檢查", "錯誤"]
        }
    ]
    
    success_count = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n測試案例 {i}:")
        print(f"  原文: {test['input']}")
        
        corrected = processor.correct_ocr_errors(test['input'])
        print(f"  修正: {corrected}")
        
        # 簡單驗證（檢查關鍵詞是否出現）
        has_improvement = any(kw in corrected for kw in test['expected_keywords'])
        
        if has_improvement:
            print("  ✅ 修正成功")
            success_count += 1
        else:
            print("  ⚠️  修正效果待確認")
    
    print(f"\n總結: {success_count}/{len(test_cases)} 個案例通過驗證")
    return success_count == len(test_cases)


def test_structured_extraction():
    """測試結構化資料提取"""
    print("\n" + "=" * 70)
    print("測試 2：結構化資料提取")
    print("=" * 70)
    
    processor = SemanticProcessor(llm_provider="ollama")
    
    if not processor.is_enabled():
        print("❌ Ollama 服務未啟動")
        return False
    
    # 模擬名片 OCR 結果
    business_card = """
    張小明
    高級軟體工程師
    ABC科技股份有限公司
    電話：(02) 2345-6789
    手機：0912-345-678
    Email: xiaoming@abc-tech.com
    台北市大安區敦化南路二段123號5樓
    """
    
    schema = {
        "name": "姓名",
        "title": "職稱", 
        "company": "公司",
        "phone": "電話",
        "mobile": "手機",
        "email": "電子郵件",
        "address": "地址"
    }
    
    print(f"\n輸入文字:\n{business_card}")
    print(f"\nSchema: {list(schema.keys())}")
    
    result = processor.extract_structured_data(business_card, schema)
    
    if result:
        print("\n✅ 提取成功:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        return True
    else:
        print("\n❌ 提取失敗")
        return False


def test_summary():
    """測試文件摘要"""
    print("\n" + "=" * 70)
    print("測試 3：文件摘要生成")
    print("=" * 70)
    
    processor = SemanticProcessor(llm_provider="ollama")
    
    if not processor.is_enabled():
        print("❌ Ollama 服務未啟動")
        return False
    
    long_text = """
    PaddleOCR Toolkit 2.0 是一個全面升級的 OCR 工具包，採用模組化架構設計。
    主要特點包括：5 個專業 Processor（HybridPDFProcessor、BasicProcessor、
    StructureProcessor、FormulaProcessor、TranslationProcessor），
    輕量級 Facade API，100% 向後相容，測試覆蓋率達 89%。
    
    v3.0 版本計畫引入 AI 增強功能，包括 SemanticProcessor 語義處理器、
    多語言自動偵測、互動式校對 UI 等創新功能。SemanticProcessor 利用
    大型語言模型（LLM）自動修正 OCR 錯誤，預期可提升識別準確率 15% 以上。
    
    該專案已在 GitHub 開源，提供完整的技術文件、API 指南、遷移指南
    和測試指南，方便開發者快速上手使用。
    """
    
    print(f"\n原文長度: {len(long_text)} 字")
    print(f"原文:\n{long_text}")
    
    summary = processor.summarize_document(long_text, max_length=80)
    
    print(f"\n摘要長度: {len(summary)} 字")
    print(f"摘要:\n{summary}")
    
    if summary and len(summary) <= 100:
        print("\n✅ 摘要生成成功")
        return True
    else:
        print("\n❌ 摘要生成失敗")
        return False


def main():
    """主測試函數"""
    print("\n🔬 SemanticProcessor 功能測試\n")
    
    results = {
        "OCR錯誤修正": test_basic_correction(),
        "結構化提取": test_structured_extraction(),
        "文件摘要": test_summary(),
    }
    
    # 總結
    print("\n" + "=" * 70)
    print("測試總結")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"  {test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！SemanticProcessor 工作正常！")
    elif passed > 0:
        print("\n⚠️  部分測試通過，請檢查失敗的測試項目")
    else:
        print("\n❌ 所有測試失敗，請確保 Ollama 服務正在運行")


if __name__ == "__main__":
    main()
