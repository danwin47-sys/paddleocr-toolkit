from paddleocr import PaddleOCR
import inspect

ocr = PaddleOCR(use_angle_cls=True, lang="ch")
print("PaddleOCR.ocr signature:")
print(inspect.signature(ocr.ocr))
