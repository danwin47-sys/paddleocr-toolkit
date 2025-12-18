# -*- coding: utf-8 -*-
"""
SemanticProcessor 使用範例

展示如何使用語義處理器進行 OCR 後處理
"""

from paddleocr_toolkit.processors.semantic_processor import SemanticProcessor


def example_1_basic_correction():
    """範例 1：基本錯誤修正"""
    print("=" * 60)
    print("範例 1：基本OCR錯誤修正")
    print("=" * 60)
    
    # 初始化語義處理器
    processor = SemanticProcessor(
        llm_provider="ollama",
        model="qwen2.5:7b"
    )
    
    # 模擬 OCR 識別結果（含錯誤）
    ocr_text = """
    這個文建包含銷多常見的OCR銷別字。
    例如："文建"應讀是"文件"，"銷別字"應讀是"錯別字"。
    通過LLM可以自動修正這些錯沒。
    """
    
    print(f"\n原始文字：\n{ocr_text}")
    
    # 修正錯誤
    if processor.is_enabled():
        corrected_text = processor.correct_ocr_errors(ocr_text)
        print(f"\n修正後：\n{corrected_text}")
    else:
        print("\n[警告] Ollama 服務不可用，請確保 Ollama 正在運行")


def example_2_structured_extraction():
    """範例 2：結構化資料提取"""
    print("\n" + "=" * 60)
    print("範例 2：從 OCR 文字提取結構化資料")
    print("=" * 60)
    
    processor = SemanticProcessor(llm_provider="ollama")
    
    # OCR 識別的名片內容
    business_card_text = """
    王小明
    資深軟體工程師
    公司：科技創新股份有限公司
    電話：02-1234-5678
    Email: xiaoming.wang@techcompany.com
    地址：台北市信義區信義路五段7號
    """
    
    # 定義提取 Schema
    schema = {
        "name": "姓名",
        "title": "職稱",
        "company": "公司名稱",
        "phone": "電話號碼",
        "email": "電子郵件",
        "address": "地址"
    }
    
    print(f"\n原始文字：\n{business_card_text}")
    print(f"\nSchema: {schema}")
    
    if processor.is_enabled():
        structured_data = processor.extract_structured_data(
            business_card_text,
            schema,
            language="zh"
        )
        print(f"\n提取結果：")
        for key, value in structured_data.items():
            print(f"  {key}: {value}")
    else:
        print("\n[警告] Ollama 服務不可用")


def example_3_document_summary():
    """範例 3：文件摘要"""
    print("\n" + "=" * 60)
    print("範例 3：生成文件摘要")
    print("=" * 60)
    
    processor = SemanticProcessor(llm_provider="ollama")
    
    # 長篇文件內容
    long_document = """
    PaddleOCR Toolkit 是一個功能強大的光學字元識別工具包，
    基於百度的 PaddleOCR 引擎開發。它支援多種識別模式，包括
    基本文字識別、混合模式（版面分析+精確OCR）、結構化識別
    （表格提取）以及數學公式識別。
    
    本工具包採用模組化架構，將不同的功能封裝在專業的處理器中，
    包括 HybridPDFProcessor、BasicProcessor、StructureProcessor、
    FormulaProcessor 和 TranslationProcessor。每個處理器負責
    特定的任務，便於維護和擴充。
    
    v3.0 版本引入了語義處理器（SemanticProcessor），利用大型
    語言模型（LLM）自動修正 OCR 錯誤，提升識別準確率 15%+。
    此外還支援多語言自動偵測、結構化資料提取和文件摘要生成等
    進階功能。
    
    該工具包已在 GitHub 上開源，並提供完整的文件和範例程式碼，
    方便開發者快速上手。
    """
    
    print(f"\n原始文件（{len(long_document)} 字）：\n{long_document}")
    
    if processor.is_enabled():
        summary = processor.summarize_document(long_document, max_length=100)
        print(f"\n摘要（{len(summary)} 字）：\n{summary}")
    else:
        print("\n[警告] Ollama 服務不可用")


def example_4_integration_with_ocr():
    """範例 4：整合到 OCR 流程"""
    print("\n" + "=" * 60)
    print("範例 4：整合到完整的 OCR 流程")
    print("=" * 60)
    
    print("""
演示如何將 SemanticProcessor 整合到完整的 OCR 處理流程：

1. 使用 BasicProcessor 進行 OCR 識別
2. 使用 SemanticProcessor 修正錯誤
3. 匯出最終結果

程式碼範例：
```python
from paddleocr_toolkit.core import OCREngineManager
from paddleocr_toolkit.processors import BasicProcessor, SemanticProcessor

# 初始化
engine = OCREngineManager(mode="basic")
engine.init_engine()

basic_processor = BasicProcessor(engine)
semantic_processor = SemanticProcessor(llm_provider="ollama")

# OCR 識別
ocr_result = basic_processor.process_image("document.jpg")
raw_text = basic_processor.get_text(ocr_result['ocr_results'])

# 語義修正
corrected_text = semantic_processor.correct_ocr_errors(raw_text)

# 匯出結果
with open("output.txt", "w", encoding="utf-8") as f:
    f.write(corrected_text)
```
    """)


if __name__ == "__main__":
    print("SemanticProcessor 使用範例\n")
    
    # 執行所有範例
    example_1_basic_correction()
    example_2_structured_extraction()
    example_3_document_summary()
    example_4_integration_with_ocr()
    
    print("\n" + "=" * 60)
    print("範例執行完畢！")
    print("=" * 60)
