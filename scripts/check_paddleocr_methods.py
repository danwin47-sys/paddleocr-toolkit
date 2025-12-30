from paddleocr import PaddleOCR
print("Checking PaddleOCR methods...")
ocr = PaddleOCR(use_angle_cls=True, lang="ch")
print(f"Has 'ocr': {hasattr(ocr, 'ocr')}")
print(f"Has 'predict': {hasattr(ocr, 'predict')}")
print(f"Dir: {dir(ocr)}")
