# Security Hardening Guide - PaddleOCR Toolkit

## Overview
This guide documents the security improvements made to the PaddleOCR Toolkit API in response to the security audit.

## Changes Made

### 1. Path Traversal Protection
**Issue**: User-provided filenames were not sanitized, allowing potential directory traversal attacks.

**Fix**: All file operations now use `Path(filename).name` to extract only the filename component:

```python
# Before (VULNERABLE)
file_path = UPLOAD_DIR / filename

# After (SECURE)
safe_filename = Path(filename).name
file_path = UPLOAD_DIR / safe_filename

# Additional validation
if not file_path.resolve().is_relative_to(UPLOAD_DIR.resolve()):
    raise HTTPException(status_code=400, detail="Invalid file path")
```

**Affected Endpoints**:
- `POST /api/ocr`
- `GET /api/files/{filename}/download`
- `DELETE /api/files/{filename}`

### 2. API Key Authentication
**Issue**: No authentication mechanism, allowing unrestricted access to OCR services.

**Fix**: Implemented API Key authentication using FastAPI's security utilities:

```python
from fastapi import Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key
```

**Usage**: Add `X-API-Key` header to all API requests:
```bash
curl -X POST http://localhost:8000/api/ocr \
  -H "X-API-Key: your-secret-key" \
  -F "file=@document.pdf"
```

### 3. Environment-Based Configuration
**Issue**: Sensitive configuration hardcoded in source code.

**Fix**: Created `.env.example` template and use `python-dotenv` to load configuration:

```python
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("API_KEY", "dev-key-change-in-production")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
```

**Setup**:
1. Copy `.env.example` to `.env`
2. Generate a strong API key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
3. Update `.env` with your configuration

### 4. CORS Hardening
**Issue**: Wildcard CORS allowed any origin to access the API.

**Fix**: CORS origins now configurable via environment variable:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # From .env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Deployment Checklist

- [ ] Copy `.env.example` to `.env`
- [ ] Generate and set a strong `API_KEY`
- [ ] Configure `ALLOWED_ORIGINS` for your domain
- [ ] Ensure `.env` is in `.gitignore`
- [ ] Test API with authentication
- [ ] Review file upload directory permissions
- [ ] Enable HTTPS in production

## Testing

Test path traversal protection:
```bash
# Should fail with 400 Bad Request
curl -X GET "http://localhost:8000/api/files/..%2F..%2Fconfig.yaml/download" \
  -H "X-API-Key: your-key"
```

Test authentication:
```bash
# Should fail with 401 Unauthorized
curl -X POST http://localhost:8000/api/ocr \
  -F "file=@test.pdf"

# Should succeed
curl -X POST http://localhost:8000/api/ocr \
  -H "X-API-Key: your-key" \
  -F "file=@test.pdf"
```

## Remaining Recommendations

1. **Plugin Directory Protection**: Ensure the `plugins/` directory is read-only for the web server process.
2. **Rate Limiting**: Consider adding rate limiting to prevent abuse.
3. **Audit Logging**: Log all API access for security monitoring.
4. **HTTPS**: Always use HTTPS in production environments.
