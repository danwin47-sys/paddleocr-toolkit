import inspect

from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang="ch")
print("PaddleOCR.ocr signature:")
print(inspect.signature(ocr.ocr))
