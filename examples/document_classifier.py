#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📄 文档分类器 - PaddleOCR Toolkit 示例项目
自动分类扫描文档类型

使用方法:
    python document_classifier.py documents/
"""

import sys
from pathlib import Path
from typing import Dict, List
import json
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

from paddle_ocr_tool import PaddleOCRTool


class DocumentClassifier:
    """文档分类器"""
    
    # 文档类型特征关键词
    DOCUMENT_PATTERNS = {
        "invoice": ["发票", "Invoice", "税号", "Tax", "金额", "Amount"],
        "contract": ["合同", "Contract", "甲方", "乙方", "Party A", "Party B"],
        "resume": ["简历", "Resume", "教育", "Education", "工作经验", "Experience"],
        "report": ["报告", "Report", "摘要", "Abstract", "结论", "Conclusion"],
        "certificate": ["证书", "Certificate", "认证", "颁发", "Issued"],
        "id_card": ["身份证", "ID Card", "姓名", "Name", "性别", "Gender"],
        "business_card": ["名片", "职位", "Position", "电话", "Tel", "Email"],
        "letter": ["信函", "Letter", "敬启", "Dear", "此致", "Sincerely"],
    }
    
    def __init__(self):
        """初始化OCR引擎"""
        print("初始化文档分类器...")
        self.ocr_tool = PaddleOCRTool(mode="basic")
        print("就绪!\n")
    
    def classify_document(self, image_path: str) -> Dict:
        """
        分类文档
        
        Args:
            image_path: 文档图片路径
            
        Returns:
            分类结果字典
        """
        print(f"分类文档: {image_path}")
        
        # OCR识别
        results = self.ocr_tool.process_image(image_path)
        
        # 合并文字
        all_text = " ".join([r.text for r in results])
        
        # 分类
        doc_type, confidence = self._classify_text(all_text)
        
        return{
            "file": str(image_path),
            "type": doc_type,
            "confidence": confidence,
            "text_length": len(all_text),
            "ocr_results_count": len(results)
        }
    
    def _classify_text(self, text: str) -> tuple:
        """分类文字"""
        scores = {}
        
        for doc_type, keywords in self.DOCUMENT_PATTERNS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[doc_type] = score
        
        if not scores:
            return "unknown", 0.0
        
        # 找出得分最高的类型
        best_type = max(scores, key=scores.get)
        max_score = scores[best_type]
        total_keywords = len(self.DOCUMENT_PATTERNS[best_type])
        
        confidence = max_score / total_keywords
        
        return best_type, confidence
    
    def batch_classify(self, directory: Path) -> List[Dict]:
        """批次分类"""
        results = []
        
        image_files = list(directory.glob("*.jpg")) + \
                     list(directory.glob("*.png")) + \
                     list(directory.glob("*.jpeg"))
        
        if not image_files:
            print("未找到图片文件")
            return results
        
        print(f"找到 {len(image_files)} 个文件\n")
        
        for i, img_file in enumerate(image_files, 1):
            print(f"[{i}/{len(image_files)}]")
            result = self.classify_document(str(img_file))
            results.append(result)
            
            print(f"  类型: {result['type']}")
            print(f"  信心度: {result['confidence']:.1%}\n")
        
        return results
    
    def organize_by_type(self, results: List[Dict], output_dir: Path):
        """按类型组织文件"""
        output_dir.mkdir(exist_ok=True)
        
        # 按类型分组
        by_type = {}
        for result in results:
            doc_type = result['type']
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(result['file'])
        
        # 创建类型目录并移动文件
        for doc_type, files in by_type.items():
            type_dir = output_dir / doc_type
            type_dir.mkdir(exist_ok=True)
            
            print(f"\n{doc_type}: {len(files)} 个文件")
            for file_path in files:
                print(f"  - {Path(file_path).name}")


def main():
    """主程序"""
    if len(sys.argv) < 2:
        print("使用方法: python document_classifier.py <图片或资料夹>")
        return
    
    input_path = Path(sys.argv[1])
    classifier = DocumentClassifier()
    
    if input_path.is_file():
        # 单个文件
        result = classifier.classify_document(str(input_path))
        print(f"\n类型: {result['type']}")
        print(f"信心度: {result['confidence']:.1%}")
        
    elif input_path.is_dir():
        # 批次分类
        results = classifier.batch_classify(input_path)
        
        # 保存结果
        with open("classification_results.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 统计
        print("\n" + "="*50)
        print("分类统计")
        print("="*50)
        
        type_counts = {}
        for result in results:
            doc_type = result['type']
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        for doc_type, count in sorted(type_counts.items()):
            print(f"{doc_type}: {count}")
        
        print("="*50)
        
        # 询问是否组织文件
        print("\n按类型组织文件到output/目录？(y/n): ", end='')
        if input().lower() == 'y':
            classifier.organize_by_type(results, Path("output"))
            print("组织完成！")


if __name__ == "__main__":
    main()
