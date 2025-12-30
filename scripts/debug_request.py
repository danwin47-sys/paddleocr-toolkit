import urllib.request
import urllib.parse
import uuid

url = "http://127.0.0.1:8000/api/ocr?mode=basic"
boundary = uuid.uuid4().hex
headers = {
    "Content-Type": f"multipart/form-data; boundary={boundary}"
}

data = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="test.png"\r\n'
    f"Content-Type: image/png\r\n\r\n"
).encode("utf-8")

with open("debug_image.png", "rb") as f:
    data += f.read()

data += f"\r\n--{boundary}--\r\n".encode("utf-8")

print(f"Sending request to {url}...")
try:
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req) as response:
        print(f"Status: {response.status}")
        print(f"Response: {response.read().decode()}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} {e.reason}")
    print(f"Error Body: {e.read().decode()}")
except Exception as e:
    print(f"Error: {e}")
