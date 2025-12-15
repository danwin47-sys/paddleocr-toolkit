#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件載入器
動態載入和管理插件
"""

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Optional

from .base import OCRPlugin


class PluginLoader:
    """
    插件載入器

    負責發現、載入和管理插件
    """

    def __init__(self, plugin_dir: str = "plugins"):
        """
        初始化插件載入器

        Args:
            plugin_dir: 插件目錄路徑
        """
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, OCRPlugin] = {}
        self.logger = logging.getLogger("PluginLoader")

    def discover_plugins(self) -> List[str]:
        """
        發現插件目錄中的所有插件

        Returns:
            插件檔案路徑列表
        """
        if not self.plugin_dir.exists():
            self.logger.warning(f"插件目錄不存在: {self.plugin_dir}")
            return []

        plugin_files = []

        # 查找所有.py檔案
        for py_file in self.plugin_dir.glob("*.py"):
            # 跳過__init__.py和以_開頭的檔案
            if py_file.name.startswith("_"):
                continue

            plugin_files.append(str(py_file))
            self.logger.debug(f"發現插件檔案: {py_file.name}")

        return plugin_files

    def load_plugin_from_file(self, file_path: str) -> Optional[OCRPlugin]:
        """
        從檔案載入插件

        Args:
            file_path: 插件檔案路徑

        Returns:
            插件實例，如果載入失敗則返回None
        """
        try:
            # 載入模組
            module_name = Path(file_path).stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)

            if spec is None or spec.loader is None:
                self.logger.error(f"無法載入插件: {file_path}")
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找OCRPlugin的子類
            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                # 檢查是否為OCRPlugin子類（且不是OCRPlugin本身）
                if (
                    isinstance(attr, type)
                    and issubclass(attr, OCRPlugin)
                    and attr != OCRPlugin
                ):
                    # 實例化插件
                    plugin = attr()

                    # 初始化插件
                    if plugin.initialize():
                        self.logger.info(f"成功載入插件: {plugin.name} v{plugin.version}")
                        return plugin
                    else:
                        self.logger.warning(f"插件初始化失敗: {plugin.name}")
                        return None

            self.logger.warning(f"在 {file_path} 中未找到插件類別")
            return None

        except Exception as e:
            self.logger.error(f"載入插件時發生錯誤 {file_path}: {e}")
            return None

    def load_all_plugins(self) -> int:
        """
        載入所有發現的插件

        Returns:
            成功載入的插件數量
        """
        plugin_files = self.discover_plugins()
        loaded_count = 0

        for file_path in plugin_files:
            plugin = self.load_plugin_from_file(file_path)

            if plugin:
                self.plugins[plugin.name] = plugin
                loaded_count += 1

        self.logger.info(f"已載入 {loaded_count}/{len(plugin_files)} 個插件")
        return loaded_count

    def get_plugin(self, name: str) -> Optional[OCRPlugin]:
        """
        取得指定名稱的插件

        Args:
            name: 插件名稱

        Returns:
            插件實例，如果不存在則返回None
        """
        return self.plugins.get(name)

    def get_all_plugins(self) -> Dict[str, OCRPlugin]:
        """取得所有已載入的插件"""
        return self.plugins.copy()

    def enable_plugin(self, name: str) -> bool:
        """
        啟用插件

        Args:
            name: 插件名稱

        Returns:
            是否成功啟用
        """
        plugin = self.get_plugin(name)
        if plugin:
            plugin.enable()
            return True
        return False

    def disable_plugin(self, name: str) -> bool:
        """
        停用插件

        Args:
            name: 插件名稱

        Returns:
            是否成功停用
        """
        plugin = self.get_plugin(name)
        if plugin:
            plugin.disable()
            return True
        return False

    def unload_plugin(self, name: str) -> bool:
        """
        卸載插件

        Args:
            name: 插件名稱

        Returns:
            是否成功卸載
        """
        plugin = self.plugins.pop(name, None)
        if plugin:
            plugin.on_shutdown()
            self.logger.info(f"已卸載插件: {name}")
            return True
        return False

    def unload_all_plugins(self) -> None:
        """卸載所有插件"""
        for plugin_name in list(self.plugins.keys()):
            self.unload_plugin(plugin_name)

    def get_plugin_info(self, name: str) -> Optional[Dict]:
        """取得插件資訊"""
        plugin = self.get_plugin(name)
        return plugin.get_info() if plugin else None

    def list_plugins(self) -> List[Dict]:
        """列出所有插件資訊"""
        return [plugin.get_info() for plugin in self.plugins.values()]


# 使用範例
if __name__ == "__main__":
    print("插件載入器")
    print("\n使用方法:")
    print(
        """
from paddleocr_toolkit.plugins.loader import PluginLoader

# 建立載入器
loader = PluginLoader('plugins/')

# 載入所有插件
loader.load_all_plugins()

# 列出插件
for info in loader.list_plugins():
    print(f"- {info['name']} v{info['version']}")

# 使用插件
plugin = loader.get_plugin('MyPlugin')
if plugin:
    processed = plugin.process_before_ocr(image)
"""
    )
