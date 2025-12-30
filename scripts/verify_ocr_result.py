import sys
import time
import uuid

import requests

BASE_URL = "http://localhost:8000/api"


def verify_ocr():
    # 1. Create dummy image
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (400, 100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 40), "Hello PaddleOCR Verification", fill=(0, 0, 0))
    img.save("verify_image.png")

    # 2. Upload
    print("Uploading file...")
    with open("verify_image.png", "rb") as f:
        files = {"file": ("verify.png", f, "image/png")}
        try:
            res = requests.post(
                f"{BASE_URL}/ocr", params={"mode": "basic"}, files=files
            )
            res.raise_for_status()
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to backend. Is it running?")
            return

    task_id = res.json()["task_id"]
    print(f"Task ID: {task_id}")

    # 3. Poll
    print("Polling for results...")
    for _ in range(20):  # Try for 20 seconds
        res = requests.get(f"{BASE_URL}/tasks/{task_id}")
        data = res.json()
        status = data.get("status")
        progress = data.get("progress")
        print(f"Status: {status}, Progress: {progress}%")

        if status == "completed":
            result = data.get("results", {})
            raw_text = result.get("raw_result", "")
            print("\n=== SUCCESS ===")
            print(f"Confidence: {result.get('confidence')}")
            print(f"Extracted Text: {raw_text}")

            if "Hello" in raw_text or "PaddleOCR" in raw_text:
                print("\n✅ Verification Passed: Text correctly extracted.")
            else:
                print(
                    "\n⚠️ Verification Warning: Text extraction might be empty or incorrect."
                )
            return

        if status == "failed":
            print(f"\n❌ Task Failed: {data.get('error')}")
            return

        time.sleep(1)

    print("\n❌ Verification Timed Out")


if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        import os

        os.system("pip install requests")
        import requests

    verify_ocr()
