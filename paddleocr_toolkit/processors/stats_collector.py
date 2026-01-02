# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 處理統計報告
統計收集器模組
用於收集和分析 OCR 處理統計數據
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from paddleocr_toolkit.utils.logger import logger


@dataclass
class PageStats:
    """單頁統計資料"""

    page_num: int
    char_count: int = 0
    word_count: int = 0
    line_count: int = 0
    avg_confidence: float = 0.0
    process_time: float = 0.0  # 秒

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_num": self.page_num,
            "char_count": self.char_count,
            "word_count": self.word_count,
            "line_count": self.line_count,
            "avg_confidence": round(self.avg_confidence, 3),
            "process_time": round(self.process_time, 3),
        }


@dataclass
class ProcessingStats:
    """OCR 處理統計資料"""

    input_file: str
    mode: str = "unknown"
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_pages: int = 0
    processed_pages: int = 0
    total_chars: int = 0
    total_words: int = 0
    total_lines: int = 0
    avg_confidence: float = 0.0
    page_stats: List[PageStats] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def total_time(self) -> float:
        """總處理時間（秒）"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()

    @property
    def pages_per_second(self) -> float:
        """每秒處理頁數"""
        if self.total_time > 0:
            return self.processed_pages / self.total_time
        return 0.0

    @property
    def chars_per_page(self) -> float:
        """每頁平均字數"""
        if self.processed_pages > 0:
            return self.total_chars / self.processed_pages
        return 0.0

    def finish(self):
        """標記處理完成"""
        self.end_time = datetime.now()

    def add_page(self, stats: PageStats):
        """新增頁面統計"""
        self.page_stats.append(stats)
        self.processed_pages += 1
        self.total_chars += stats.char_count
        self.total_words += stats.word_count
        self.total_lines += stats.line_count

        # 更新平均信賴度
        if stats.avg_confidence > 0:
            total_conf = (
                self.avg_confidence * (self.processed_pages - 1) + stats.avg_confidence
            )
            self.avg_confidence = total_conf / self.processed_pages

    def add_error(self, error: str):
        """記錄錯誤"""
        self.errors.append(error)

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "input_file": self.input_file,
            "mode": self.mode,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_time_seconds": round(self.total_time, 2),
            "total_pages": self.total_pages,
            "processed_pages": self.processed_pages,
            "total_chars": self.total_chars,
            "total_words": self.total_words,
            "total_lines": self.total_lines,
            "avg_confidence": round(self.avg_confidence, 3),
            "pages_per_second": round(self.pages_per_second, 2),
            "chars_per_page": round(self.chars_per_page, 1),
            "errors": self.errors,
            "page_stats": [p.to_dict() for p in self.page_stats],
        }

    def to_summary(self) -> str:
        """生成摘要報告"""
        lines = [
            "=" * 50,
            "OCR 處理統計報告",
            "=" * 50,
            f"檔案：{self.input_file}",
            f"模式：{self.mode}",
            f"處理時間：{self.total_time:.2f} 秒",
            "",
            f"總頁數：{self.total_pages}",
            f"已處理：{self.processed_pages} 頁",
            f"處理速度：{self.pages_per_second:.2f} 頁/秒",
            "",
            f"總字數：{self.total_chars:,}",
            f"總詞數：{self.total_words:,}",
            f"總行數：{self.total_lines:,}",
            f"每頁平均：{self.chars_per_page:.0f} 字",
            "",
            f"平均信賴度：{self.avg_confidence:.1%}",
        ]

        if self.errors:
            lines.extend(["", f"錯誤數：{len(self.errors)}", "錯誤列表："])
            for e in self.errors[:5]:
                lines.append(f"  - {e}")
            if len(self.errors) > 5:
                lines.append(f"  ... 還有 {len(self.errors) - 5} 個錯誤")

        lines.append("=" * 50)
        return "\n".join(lines)

    def print_summary(self):
        """列印摘要報告"""
        print(self.to_summary())

    def save_report(self, output_path: str, format: str = "txt"):
        """
        儲存統計報告

        Args:
            output_path: 輸出路徑
            format: 格式 ("txt", "json")
        """
        import json

        if format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(self.to_summary())

        logging.info(f"統計報告已儲存：{output_path}")


class StatsCollector:
    """
    統計收集器 - 追蹤 OCR 處理過程
    """

    def __init__(self, input_file: str, mode: str = "unknown", total_pages: int = 0):
        """初始化統計收集器"""
        self.stats = ProcessingStats(
            input_file=input_file, mode=mode, total_pages=total_pages
        )
        self._current_page_start: Optional[float] = None

    def start_page(self, page_num: int):
        """開始處理頁面"""
        self._current_page_start = time.time()
        self._current_page_num = page_num

    def finish_page(
        self,
        page_num: int,
        text: str = "",
        ocr_results: Optional[List[Any]] = None,
        confidence_values: Optional[List[float]] = None,
    ):
        """
        完成頁面處理

        Args:
            page_num: 頁碼
            text: 識別的文字
            ocr_results: OCR 結果列表
            confidence_values: 信賴度列表
        """
        process_time = 0.0
        if self._current_page_start:
            process_time = time.time() - self._current_page_start

        # 計算統計
        char_count = len(text.replace(" ", "").replace("\n", ""))
        word_count = len(text.split()) if text else 0
        line_count = len(text.split("\n")) if text else 0

        avg_conf = 0.0
        if confidence_values:
            avg_conf = sum(confidence_values) / len(confidence_values)
        elif ocr_results:
            confs = [r.confidence for r in ocr_results if hasattr(r, "confidence")]
            if confs:
                avg_conf = sum(confs) / len(confs)

        page_stats = PageStats(
            page_num=page_num,
            char_count=char_count,
            word_count=word_count,
            line_count=line_count,
            avg_confidence=avg_conf,
            process_time=process_time,
        )

        self.stats.add_page(page_stats)

    def add_error(self, error: str):
        """記錄錯誤"""
        self.stats.add_error(error)

    def finish(self) -> ProcessingStats:
        """完成處理並返回統計"""
        self.stats.finish()
        return self.stats

    def get_stats(self) -> ProcessingStats:
        """取得當前統計"""
        return self.stats
