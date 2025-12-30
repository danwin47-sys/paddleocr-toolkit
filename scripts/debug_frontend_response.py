import time

import requests
from PIL import Image, ImageDraw

# Create test image
img = Image.new("RGB", (400, 100), color=(255, 255, 255))
d = ImageDraw.Draw(img)
d.text((10, 40), "測試文字 Test Text", fill=(0, 0, 0))
img.save("test_frontend.png")

# Upload
print("上傳檔案...")
with open("test_frontend.png", "rb") as f:
    files = {"file": ("test.png", f, "image/png")}
    res = requests.post(
        "http://localhost:8000/api/ocr", params={"mode": "basic"}, files=files
    )

task_id = res.json()["task_id"]
print(f"Task ID: {task_id}")

# Poll
for i in range(20):
    time.sleep(1)
    res = requests.get(f"http://localhost:8000/api/tasks/{task_id}")
    data = res.json()
    print(f"\n輪詢 #{i+1}:")
    print(f"Status: {data.get('status')}")
    print(f"Progress: {data.get('progress')}")

    if data.get("status") == "completed":
        print("\n完整回應:")
        import json

        print(json.dumps(data, indent=2, ensure_ascii=False))

        print("\n檢查 results 字段:")
        results = data.get("results")
        if results:
            print(f"  - raw_result: {results.get('raw_result')}")
            print(f"  - pages: {results.get('pages')}")
            print(f"  - confidence: {results.get('confidence')}")
        else:
            print("  ❌ results 字段為空！")
        break

    if data.get("status") == "failed":
        print(f"錯誤: {data.get('error')}")
        break
