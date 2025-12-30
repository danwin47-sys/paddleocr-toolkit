from paddleocr import PaddleOCR
from PIL import Image, ImageDraw

# Create dummy image
img = Image.new('RGB', (400, 100), color=(255, 255, 255))
d = ImageDraw.Draw(img)
d.text((10, 40), "Hello PaddleOCR", fill=(0, 0, 0))
img.save('debug_image_script.png')

print("Initializing PaddleOCR...")
ocr = PaddleOCR(use_angle_cls=True, lang="ch")
print("Predicting...")
result = ocr.ocr('debug_image_script.png', cls=True)

print(f"Result Type: {type(result)}")
print(f"Result Content: {result}")

if isinstance(result, list):
    for i, item in enumerate(result):
        print(f"Item {i} Type: {type(item)}")
        print(f"Item {i} Content: {item}")
