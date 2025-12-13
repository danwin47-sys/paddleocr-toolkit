# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.0.0] - 2024-12-13

### Added

- 🎉 Initial release
- PDF compression with JPEG quality control (`--no-compress`, `--jpeg-quality`)
- StatsCollector for processing statistics display
- OCRWorkaround fallback for scanned document translation (`--ocr-workaround`)
- GitHub Actions CI with syntax checking and test coverage
- ARCHITECTURE.md blueprint documentation
- Unit tests for core modules (27 tests)

### Changed

- Refactored to use `paddleocr_toolkit` package modules
- Removed 600+ lines of duplicate code
- Optimized `_process_hybrid_pdf` to use `add_page_from_pixmap` directly

### Fixed

- PDF compression not being applied (method call mismatch)
- English spacing issues with ordinal numbers (e.g., "9th")

## [0.9.0] - 2024-12-12

### Added

- Hybrid mode with PP-StructureV3 + PP-OCRv5
- Translation support with Ollama local models
- Bilingual PDF output (alternating/side-by-side)
- HTML output format for hybrid mode
- `--all` flag for outputting all formats

## [0.8.0] - 2024-12-11

### Added

- `fix_english_spacing()` for OCR text correction
- `detect_pdf_quality()` for automatic DPI adjustment
- Support for scanned PDF detection

## [0.7.0] - 2024-12-10

### Added

- Searchable PDF generation with transparent text layer
- PP-StructureV3 support for structured document parsing
- PaddleOCR-VL support for visual language understanding
- PP-FormulaNet support for mathematical formula recognition
