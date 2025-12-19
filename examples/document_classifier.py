#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📄 文件分類器 - PaddleOCR Toolkit 示例專案
自動分類掃描文件型別

使用方法:
    python document_classifier.py documents/
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from paddle_ocr_tool import PaddleOCRTool


class DocumentClassifier:
    """檔案分類器"""

    # 檔案型別特徵關鍵詞
    DOCUMENT_PATTERNS = {
        "invoice": ["發票", "Invoice", "稅號", "Tax", "金額", "Amount"],
        "contract": ["合約", "Contract", "甲方", "乙方", "Party A", "Party B"],
        "resume": ["履歷", "Resume", "教育", "Education", "工作經驗", "Experience"],
        "report": ["報告", "Report", "摘要", "Abstract", "結論", "Conclusion"],
        "certificate": ["證書", "Certificate", "認證", "頒發", "Issued"],
        "id_card": ["身分證", "ID Card", "姓名", "Name", "性別", "Gender"],
        "business_card": ["名片", "職位", "Position", "電話", "Tel", "Email"],
        "letter": ["信函", "Letter", "敬啟", "Dear", "此致", "Sincerely"],
    }

    def __init__(self):
        """初始化OCR引擎"""
        print("初始化檔案分類器...")
        self.ocr_tool = PaddleOCRTool(mode="basic")
        print("就緒!\n")

    def classify_document(self, image_path: str) -> Dict:
        """
        分類檔案

        Args:
            image_path: 檔案圖片路徑

        Returns:
            分類結果字典
        """
        print(f"分類檔案: {image_path}")

        # OCR識別
        results = self.ocr_tool.process_image(image_path)

        # 合併文字
        all_text = " ".join([r.text for r in results])

        # 分類
        doc_type, confidence = self._classify_text(all_text)

        return {
            "file": str(image_path),
            "type": doc_type,
            "confidence": confidence,
            "text_length": len(all_text),
            "ocr_results_count": len(results),
        }

    def _classify_text(self, text: str) -> tuple:
        """分類文字"""
        scores = {}

        for doc_type, keywords in self.DOCUMENT_PATTERNS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[doc_type] = score

        if not scores:
            return "unknown", 0.0

        # 找出得分最高的型別
        best_type = max(scores, key=scores.get)
        max_score = scores[best_type]
        total_keywords = len(self.DOCUMENT_PATTERNS[best_type])

        confidence = max_score / total_keywords

        return best_type, confidence

    def batch_classify(self, directory: Path) -> List[Dict]:
        """批次分類"""
        results = []

        image_files = (
            list(directory.glob("*.jpg"))
            + list(directory.glob("*.png"))
            + list(directory.glob("*.jpeg"))
        )

        if not image_files:
            print("未找到圖片檔案")
            return results

        print(f"找到 {len(image_files)} 個檔案\n")

        for i, img_file in enumerate(image_files, 1):
            print(f"[{i}/{len(image_files)}]")
            result = self.classify_document(str(img_file))
            results.append(result)

            print(f"  型別: {result['type']}")
            print(f"  信心度: {result['confidence']:.1%}\n")

        return results

    def organize_by_type(self, results: List[Dict], output_dir: Path):
        """按型別組織檔案"""
        output_dir.mkdir(exist_ok=True)

        # 按型別分組
        by_type = {}
        for result in results:
            doc_type = result["type"]
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(result["file"])

        # 建立型別目錄並移動檔案
        for doc_type, files in by_type.items():
            type_dir = output_dir / doc_type
            type_dir.mkdir(exist_ok=True)

            print(f"\n{doc_type}: {len(files)} 個檔案")
            for file_path in files:
                print(f"  - {Path(file_path).name}")


def main():
    """主程式"""
    if len(sys.argv) < 2:
        print("使用方法: python document_classifier.py <圖片或資料夾>")
        return

    input_path = Path(sys.argv[1])
    classifier = DocumentClassifier()

    if input_path.is_file():
        # 單個檔案
        result = classifier.classify_document(str(input_path))
        print(f"\n型別: {result['type']}")
        print(f"信心度: {result['confidence']:.1%}")

    elif input_path.is_dir():
        # 批次分類
        results = classifier.batch_classify(input_path)

        # 儲存結果
        with open("classification_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # 統計
        print("\n" + "=" * 50)
        print("分類統計")
        print("=" * 50)

        type_counts = {}
        for result in results:
            doc_type = result["type"]
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

        for doc_type, count in sorted(type_counts.items()):
            print(f"{doc_type}: {count}")

        print("=" * 50)

        # 詢問是否組織檔案
        print("\n按型別組織檔案到output/目錄？(y/n): ", end="")
        if input().lower() == "y":
            classifier.organize_by_type(results, Path("output"))
            print("組織完成！")


if __name__ == "__main__":
    main()
