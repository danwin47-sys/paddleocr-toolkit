# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Comprehensive CI/CD pipeline with GitHub Actions
- Docker support with multi-stage build
- Complete contribution guidelines
- Security policy and issue templates
- End-to-end integration tests
- Business card scanner example
- Video tutorial script
- Architecture documentation

## [1.1.0] - 2024-12-15

### Added - Week 1: Test Coverage Improvement

- Extended test suite for `batch_processor` (+16 tests, coverage: 71%→74%)
- Extended test suite for `result_parser` (+18 tests, coverage: 75%→91%)
- New test suite for `streaming_utils` (+8 tests, coverage: 67%→85%)
- Total: +42 tests, overall coverage increased to 84%

### Added - Week 2: Complete Documentation

- `QUICK_START.md` - 5-minute quickstart guide
- `API_GUIDE.md` - Comprehensive API reference
- `BEST_PRACTICES.md` - Production best practices
- `FAQ.md` - 40+ common questions answered
- `TROUBLESHOOTING.md` - Complete troubleshooting guide
- `ARCHITECTURE.md` - System architecture diagrams
- `VIDEO_SCRIPT.md` - Tutorial video script

### Added - Example Tools

- Receipt scanner (`receipt_scanner.py`) - Extract invoice information
- Performance benchmark (`benchmark.py`) - Performance testing tool
- CLI beautification (`rich_ui.py`) - Rich terminal UI
- Business card scanner (`business_card_scanner.py`) - Extract contact info with vCard export

### Added - DevOps & Community

- GitHub Actions CI/CD pipeline
- Multi-stage Dockerfile for production
- docker-compose.yml configuration
- CONTRIBUTING.md guidelines
- CODE_OF_CONDUCT.md
- SECURITY.md policy
- Issue templates (bug report & feature request)
- setup.py for PyPI distribution

### Changed

- Updated project structure documentation
- Enhanced README with new features
- Improved test organization

### Fixed

- Windows encoding issues in CLI (partial)
- Test reliability improvements

## [1.0.0] - 2024-12-14

### Added - Stage 3: Modular Architecture

- Complete modular refactoring with 19 specialized modules
- CLI layer: `argument_parser`, `config_handler`, `mode_processor`, `output_manager`
- Core layer: `ocr_engine`, `result_parser`, `pdf_generator`, `pdf_utils`, `streaming_utils`, `config_loader`, `models`
- Processor layer: `batch_processor`, `pdf_processor`, `image_preprocessor`, `structure_processor`, `translation_processor`
- Output layer: `output_manager`
- Backward compatibility with legacy `paddle_ocr_tool.py`
- Graceful degradation when Stage 3 modules unavailable

### Added - Testing & Quality

- Comprehensive test suite (346 tests, 83% coverage)
- Tests for all CLI modules
- Tests for all core modules
- Tests for all processor modules
- Integration tests
- pytest configuration with coverage reporting

### Added - Documentation

- Complete project summary
- Stage 1, 2, 3 documentation
- Performance optimization plan
- Architecture diagrams
- Detailed CHANGELOG

### Changed - Performance Optimization

- Memory usage reduced by 90%
- I/O performance improved by 50%
- Batch processing optimization
- Streaming support for large files

### Changed - Code Quality

- 100% type hints coverage
- 100% docstrings coverage
- Code formatted with Black and isort
- mypy type checking enabled

## [0.9.0] - 2024-12-13

### Added - Stage 2: Performance & Quality

- Batch processing capabilities
- Image preprocessing module
- Statistics collection
- Glossary management
- Memory optimization
- Streaming utilities

### Changed

- Refactored internal structure
- Improved error handling
- Enhanced configuration management

## [0.8.0] - 2024-12-12

### Added - Stage 1: Feature Completion

- Translation support with Ollama
- Bilingual PDF generation
- Table extraction
- Layout analysis
- Formula recognition
- VL (Vision-Language) support

### Added

- Searchable PDF generation
- Multiple output formats (Markdown, JSON, HTML)
- PDF quality detection
- English spacing correction

## [0.5.0] - 2024-12-10

### Added - Initial Release

- Basic OCR functionality
- PDF processing
- Image processing
- CLI interface
- Configuration support

---

## Version Naming Convention

- **Major** (x.0.0): Breaking changes, major architecture updates
- **Minor** (0.x.0): New features, significant improvements
- **Patch** (0.0.x): Bug fixes, minor improvements

## Links

- [GitHub Repository](https://github.com/danwin47-sys/paddleocr-toolkit)
- [Issue Tracker](https://github.com/danwin47-sys/paddleocr-toolkit/issues)
- [Documentation](docs/)

---

**Note**: Dates use YYYY-MM-DD format. All times in UTC+8.
