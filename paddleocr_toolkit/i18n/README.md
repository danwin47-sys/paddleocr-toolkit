# Internationalization (i18n) Structure

PaddleOCR Toolkit internationalization framework.

---

## Supported Languages

- 🇨🇳 中文 (zh_CN) - Default
- 🇹🇼 繁體中文 (zh_TW) - ✅ Available
- 🇺🇸 English (en_US) - ✅ Available
- 🇯🇵 日本語 (ja_JP) - Planned
- 🇰🇷 한국어 (ko_KR) - Planned

---

## File Structure

```
paddleocr_toolkit/
└── i18n/
    ├── __init__.py
    ├── zh_CN.json    # Chinese (Simplified)
    ├── en_US.json    # English
    ├── ja_JP.json    # Japanese
    └── ko_KR.json    # Korean
```

---

## Usage

```python
from paddleocr_toolkit.i18n import get_text, set_language

# Set language
set_language('en_US')

# Get translated text
print(get_text('processing_pdf'))  # "Processing PDF..."
```

---

## Translation Keys

Common keys to translate:

- `processing_pdf` - "處理 PDF 中..."
- `ocr_complete` - "OCR 處理完成"
- `error_file_not_found` - "找不到檔案"
- `saving_results` - "儲存結果..."
- `batch_processing` - "批次處理中..."

---

## Contributing Translations

1. Copy `zh_CN.json`
2. Rename to your language code
3. Translate all values
4. Submit PR

---

## Future Plans

- Auto-detect system language
- CLI language selection (`--lang en`)
- Web interface i18n
- Documentation translation

---

**Status**: 📝 Framework Ready, Translations Needed
