# -*- coding: utf-8 -*-
"""
緩衝寫入工具 - I/O 優化

提供帶緩衝的文件寫入，減少 I/O 操作次數。
"""

from typing import Any, Dict, List, Optional


class BufferedWriter:
    """
    帶緩衝的文件寫入器

    優點：
    - 批次寫入減少 I/O 次數
    - 大緩衝區提升性能
    - 自動 flush 機制
    """

    def __init__(
        self,
        filepath: str,
        buffer_size: int = 1000,
        file_buffer_size: int = 1024 * 1024,  # 1MB
    ):
        """
        初始化寫入器

        Args:
            filepath: 輸出檔案路徑
            buffer_size: 行緩衝大小（預設 1000 行）
            file_buffer_size: 文件緩衝大小（預設 1MB）
        """
        self.filepath = filepath
        self.buffer: List[str] = []
        self.buffer_size = buffer_size
        self.file_buffer_size = file_buffer_size
        self.file = None

    def __enter__(self):
        """進入 context manager"""
        self.file = open(
            self.filepath, "w", encoding="utf-8", buffering=self.file_buffer_size
        )
        return self

    def write(self, text: str):
        """
        寫入文字（緩衝）

        Args:
            text: 要寫入的文字
        """
        self.buffer.append(text)

        # 達到緩衝區大小時自動 flush
        if len(self.buffer) >= self.buffer_size:
            self.flush()

    def writelines(self, lines: List[str]):
        """
        批次寫入多行

        Args:
            lines: 文字行列表
        """
        for line in lines:
            self.write(line)

    def flush(self):
        """刷新緩衝區到文件"""
        if self.buffer:
            self.file.write("\n".join(self.buffer) + "\n")
            self.buffer.clear()

    def __exit__(self, *args):
        """退出 context manager"""
        self.flush()
        if self.file:
            self.file.close()


class BufferedJSONWriter:
    """
    帶緩衝的 JSON 寫入器

    適合寫入大型 JSON 陣列。
    """

    def __init__(
        self, filepath: str, buffer_size: int = 100, indent: Optional[int] = 2
    ):
        """
        初始化 JSON 寫入器

        Args:
            filepath: 輸出檔案路徑
            buffer_size: 緩衝大小
            indent: JSON 縮排（None 為壓縮）
        """
        self.filepath = filepath
        self.buffer: List[Dict[str, Any]] = []
        self.buffer_size = buffer_size
        self.indent = indent
        self.file = None
        self.is_first = True

    def __enter__(self):
        """進入 context manager"""
        self.file = open(
            self.filepath, "w", encoding="utf-8", buffering=1024 * 1024
        )  # 1MB
        self.file.write("[\n")
        return self

    def write(self, obj: dict):
        """
        寫入 JSON 物件

        Args:
            obj: 要寫入的字典
        """
        self.buffer.append(obj)

        if len(self.buffer) >= self.buffer_size:
            self.flush()

    def flush(self):
        """刷新緩衝區"""
        if not self.buffer:
            return

        import json

        for obj in self.buffer:
            if not self.is_first:
                self.file.write(",\n")
            else:
                self.is_first = False

            json_str = json.dumps(obj, ensure_ascii=False, indent=self.indent)
            # 縮排整個物件
            if self.indent:
                indented = "\n".join("  " + line for line in json_str.split("\n"))
                self.file.write(indented)
            else:
                self.file.write(json_str)

        self.buffer.clear()

    def __exit__(self, *args):
        """退出 context manager"""
        self.flush()
        if self.file:
            self.file.write("\n]\n")
            self.file.close()


def write_text_efficient(filepath: str, lines: List[str], buffer_size: int = 1000):
    """
    高效寫入文字文件

    Args:
        filepath: 輸出檔案路徑
        lines: 文字行列表
        buffer_size: 緩衝大小

    Example:
        lines = ['line1', 'line2', ...]
        write_text_efficient('output.txt', lines)
    """
    with BufferedWriter(filepath, buffer_size=buffer_size) as writer:
        writer.writelines(lines)


def write_json_efficient(filepath: str, objects: List[dict], buffer_size: int = 100):
    """
    高效寫入 JSON 陣列

    Args:
        filepath: 輸出檔案路徑
        objects: 字典列表
        buffer_size: 緩衝大小

    Example:
        data = [{'page': 1, 'text': '...'}, ...]
        write_json_efficient('output.json', data)
    """
    with BufferedJSONWriter(filepath, buffer_size=buffer_size) as writer:
        for obj in objects:
            writer.write(obj)
