from PIL import Image, ImageDraw, ImageFont

img = Image.new("RGB", (400, 100), color=(255, 255, 255))
d = ImageDraw.Draw(img)
# 簡單畫一些文字
d.text((10, 40), "Hello PaddleOCR", fill=(0, 0, 0))
img.save("debug_image.png")
print("Created debug_image.png")
