import sys
import os
import unittest
import numpy as np
from types import SimpleNamespace

# 將 custom 目錄加入 path 以便匯入插件
sys.path.append(os.path.join(os.getcwd(), 'custom'))

try:
    from pii_masking import PIIMaskingPlugin
    from watermark_remover import WatermarkRemoverPlugin
    from doc_classifier import DocClassifierPlugin
except ImportError:
    # 如果在某些環境下找不到檔案，略過測試
    PIIMaskingPlugin = None

class TestPlugins(unittest.TestCase):
    
    def setUp(self):
        if PIIMaskingPlugin is None:
            self.skipTest("Plugin files not found in custom/ directory")

    def test_pii_masking(self):
        plugin = PIIMaskingPlugin()
        
        # 模擬 OCR 結果
        results = [
            {"text": "我的電話是 0912-345-678"},
            SimpleNamespace(text="Email: test@example.com"),
            {"text": "身分證 A123456789"},
            {"text": "普通文字"}
        ]
        
        processed = plugin.on_after_ocr(results)
        
        # 驗證手機號遮蔽
        self.assertIn("0912***678", processed[0]["text"])
        
        # 驗證 Email 遮蔽
        self.assertIn("t***@example.com", processed[1].text)
        
        # 驗證身分證遮蔽
        self.assertIn("A123******", processed[2]["text"])
        
        # 驗證普通文字未變
        self.assertEqual("普通文字", processed[3]["text"])

    def test_doc_classifier(self):
        plugin = DocClassifierPlugin()
        
        # 測試發票
        invoice_results = [{"text": "統一編號: 12345678"}, {"text": "稅額: 500"}]
        # 這裡只能驗證不會 crash，因為分類結果是印 log
        # 實務上插件應該將結果寫入 metadata，這裡我們簡單執行確保無誤
        plugin.on_after_ocr(invoice_results)
        
        # 測試合約
        contract_results = [{"text": "立合約書人"}, {"text": "甲方"}, {"text": "乙方"}]
        plugin.on_after_ocr(contract_results)

    def test_watermark_remover(self):
        try:
            import cv2
        except ImportError:
            self.skipTest("OpenCV not installed")
            
        plugin = WatermarkRemoverPlugin()
        
        # 建立一個模擬圖片 (白底黑字 + 淺灰浮水印)
        img = np.full((100, 100), 255, dtype=np.uint8)
        
        # 畫黑色文字 (0)
        cv2.rectangle(img, (10, 10), (30, 30), 0, -1)
        
        # 畫淺灰浮水印 (220)
        cv2.rectangle(img, (40, 40), (60, 60), 220, -1)
        
        # 執行處理
        processed = plugin.on_before_ocr(img)
        
        # 驗證黑色文字保留 (0)
        self.assertEqual(processed[20, 20], 0)
        
        # 驗證淺灰浮水印被去除 (變為 255)
        self.assertEqual(processed[50, 50], 255)

if __name__ == '__main__':
    unittest.main()
