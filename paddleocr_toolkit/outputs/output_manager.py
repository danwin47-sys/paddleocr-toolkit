# -*- coding: utf-8 -*-
"""
輸出管理器 - 統一管理各種格式的輸出

本模組負責：
- 統一輸出介面
- 多格式輸出支援
- 輸出路徑管理
- 批次輸出
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    from paddleocr_toolkit.core.buffered_writer import (
        BufferedJSONWriter,
        BufferedWriter,
    )
    from paddleocr_toolkit.core.models import OCRResult

    HAS_BUFFERED = True
except ImportError:
    HAS_BUFFERED = False


class OutputManager:
    """
    輸出管理器

    統一管理不同格式的輸出，支援：
    - Markdown (.md)
    - JSON (.json)
    - Text (.txt)
    - HTML (.html)
    - Excel (.xlsx)

    Example:
        manager = OutputManager(base_path='output', formats=['md', 'json'])
        manager.write_all(content={'text': 'Hello', 'results': [...]})
    """

    def __init__(
        self,
        base_path: str,
        formats: Optional[List[str]] = None,
        use_buffered: bool = True,
    ):
        """
        初始化輸出管理器

        Args:
            base_path: 基礎輸出路徑（不含副檔名）
            formats: 輸出格式列表 ['md', 'json', 'txt', 'html', 'xlsx']
            use_buffered: 是否使用緩衝寫入
        """
        self.base_path = Path(base_path)
        self.formats = set(formats) if formats else set()
        self.use_buffered = use_buffered and HAS_BUFFERED
        self.writers = {}

    def add_format(self, format_name: str) -> None:
        """添加輸出格式"""
        self.formats.add(format_name.lower())

    def remove_format(self, format_name: str) -> None:
        """移除輸出格式"""
        self.formats.discard(format_name.lower())

    def write_markdown(self, content: str, output_path: Optional[str] = None) -> str:
        """
        寫入 Markdown 格式

        Args:
            content: Markdown 內容
            output_path: 輸出路徑（可選）

        Returns:
            str: 輸出檔案路徑
        """
        if not output_path:
            output_path = f"{self.base_path}.md"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        logging.info(f"Markdown 已儲存: {output_path}")
        return output_path

    def write_json(
        self, data: Any, output_path: Optional[str] = None, indent: int = 2
    ) -> str:
        """
        寫入 JSON 格式

        Args:
            data: JSON 數據
            output_path: 輸出路徑（可選）
            indent: 縮排空格數

        Returns:
            str: 輸出檔案路徑
        """
        if not output_path:
            output_path = f"{self.base_path}.json"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if self.use_buffered and isinstance(data, list):
            # 使用緩衝寫入器
            with BufferedJSONWriter(output_path, indent=indent) as writer:
                for item in data:
                    writer.write(item)
        else:
            # 標準寫入
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)

        logging.info(f"JSON 已儲存: {output_path}")
        return output_path

    def write_text(self, content: str, output_path: Optional[str] = None) -> str:
        """
        寫入純文字格式

        Args:
            content: 文字內容
            output_path: 輸出路徑（可選）

        Returns:
            str: 輸出檔案路徑
        """
        if not output_path:
            output_path = f"{self.base_path}.txt"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        logging.info(f"文字已儲存: {output_path}")
        return output_path

    def write_html(
        self, content: str, output_path: Optional[str] = None, title: str = "OCR Result"
    ) -> str:
        """
        寫入 HTML 格式

        Args:
            content: HTML 內容（或 Markdown，會自動轉換）
            output_path: 輸出路徑（可選）
            title: HTML 標題

        Returns:
            str: 輸出檔案路徑
        """
        if not output_path:
            output_path = f"{self.base_path}.html"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 簡單 HTML 模板
        html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        pre {{ background: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    <pre>{content}</pre>
</body>
</html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        logging.info(f"HTML 已儲存: {output_path}")
        return output_path

    def write_all(self, content_dict: Dict[str, Any]) -> Dict[str, str]:
        """
        寫入所有指定格式

        Args:
            content_dict: 內容字典，應包含：
                - 'text': 純文字內容
                - 'markdown': Markdown 內容（可選）
                - 'json_data': JSON 數據（可選）
                - 'html': HTML 內容（可選）

        Returns:
            Dict[str, str]: 格式 -> 輸出路徑的映射
        """
        output_paths = {}

        for format_name in self.formats:
            try:
                if format_name == "md" and "markdown" in content_dict:
                    path = self.write_markdown(content_dict["markdown"])
                    output_paths["markdown"] = path

                elif format_name == "json" and "json_data" in content_dict:
                    path = self.write_json(content_dict["json_data"])
                    output_paths["json"] = path

                elif format_name == "txt" and "text" in content_dict:
                    path = self.write_text(content_dict["text"])
                    output_paths["text"] = path

                elif format_name == "html":
                    html_content = content_dict.get("html") or content_dict.get(
                        "text", ""
                    )
                    path = self.write_html(html_content)
                    output_paths["html"] = path

            except Exception as e:
                logging.error(f"寫入 {format_name} 格式失敗: {e}")

        return output_paths

    def get_output_path(self, format_name: str) -> str:
        """
        獲取指定格式的輸出路徑

        Args:
            format_name: 格式名稱

        Returns:
            str: 輸出路徑
        """
        return f"{self.base_path}.{format_name}"

    def cleanup(self) -> None:
        """清理資源"""
        self.writers.clear()

    def __enter__(self):
        """Context manager 支援"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 支援"""
        self.cleanup()
        return False
