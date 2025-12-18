# -*- coding: utf-8 -*-
"""
PaddleOCRFacade + SemanticProcessor 整合示範

展示如何在 Facade 中使用語義處理功能
"""

import sys
from pathlib import Path

# 加入專案根目錄
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from paddle_ocr_facade import PaddleOCRFacade


def demo_1_simple_correction():
    """示範 1：簡單的文字修正"""
    print("=" * 70)
    print("示範 1：透過 Facade 使用語義修正")
    print("=" * 70)
    
    # 啟用語義處理的 Facade
    facade = PaddleOCRFacade(
        mode="basic",
        enable_semantic=True,
        llm_provider="ollama",
        llm_model="qwen2.5:7b"
    )
    
    # 模擬 OCR 錯誤文字
    ocr_text = "這個文建包含銷多OCR銷別字"
    
    print(f"\n原文: {ocr_text}")
    
    # 使用 Facade 的 correct_text 方法
    corrected = facade.correct_text(ocr_text)
    
    print(f"修正: {corrected}")
    print("\n✅ 透過 Facade 成功修正！")


def demo_2_structured_extraction():
    """示範 2：結構化資料提取"""
    print("\n" + "=" * 70)
    print("示範 2：透過 Facade 提取結構化資料")
    print("=" * 70)
    
    facade = PaddleOCRFacade(
        mode="basic",
        enable_semantic=True
    )
    
    # 名片文字
    business_card = """
    王小明
    資深軟體工程師
    科技股份有限公司
    電話：02-1234-5678
    Email: wang@tech.com
    """
    
    schema = {
        "name": "姓名",
        "title": "職稱",
        "company": "公司",
        "phone": "電話",
        "email": "Email"
    }
    
    print(f"\n輸入文字:{business_card}")
    
    # 使用 Facade 的 extract_structured_data 方法
    result = facade.extract_structured_data(business_card, schema)
    
    if result:
        print("\n✅ 提取成功:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    else:
        print("\n❌ 提取失敗（請確認 Ollama 服務運行中）")


def demo_3_without_semantic():
    """示範 3：未啟用語義處理時的行為"""
    print("\n" + "=" * 70)
    print("示範 3：未啟用語義處理（返回原文）")
    print("=" * 70)
    
    # 不啟用語義處理
    facade = PaddleOCRFacade(
        mode="basic",
        enable_semantic=False  # 明確禁用
    )
    
    text = "這個文建有錯沒"
    
    print(f"\n原文: {text}")
    
    # 嘗試使用語義修正（會返回原文並警告）
    result = facade.correct_text(text)
    
    print(f"結果: {result}")
    print("\n⚠️  語義處理未啟用，返回原文")


def demo_4_comparison():
    """示範 4：啟用與未啟用的對比"""
    print("\n" + "=" * 70)
    print("示範 4：啟用 vs 未啟用語義處理對比")
    print("=" * 70)
    
    test_text = "PaddleOCR工見包提供強太的OCR功隨"
    
    print(f"\n測試文字: {test_text}\n")
    
    # 未啟用
    print("[ 未啟用語義處理 ]")
    facade_without = PaddleOCRFacade(mode="basic", enable_semantic=False)
    result_without = facade_without.correct_text(test_text)
    print(f"  結果: {result_without}")
    
    # 啟用
    print("\n[ 啟用語義處理 ]")
    facade_with = PaddleOCRFacade(
        mode="basic",
        enable_semantic=True,
        llm_provider="ollama"
    )
    result_with = facade_with.correct_text(test_text)
    print(f"  結果: {result_with}")
    
    print("\n📊 對比結論:")
    print(f"  - 未啟用: 原文保持不變")
    print(f"  - 已啟用: {result_with}")


if __name__ == "__main__":
    print("\n🚀 PaddleOCRFacade + SemanticProcessor 整合示範\n")
    
    demo_1_simple_correction()
    demo_2_structured_extraction()
    demo_3_without_semantic()
    demo_4_comparison()
    
    print("\n" + "=" * 70)
    print("示範完成！")
    print("=" * 70)
    print("\n💡 提示:")
    print("  - 使用 enable_semantic=True 啟用語義處理")
    print("  - 需要 Ollama 服務運行：ollama serve")
    print("  - 預設使用 qwen2.5:7b 模型")
    print("")
