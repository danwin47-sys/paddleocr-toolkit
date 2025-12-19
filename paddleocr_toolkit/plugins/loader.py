#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外掛載入器
動態載入和管理外掛
"""

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Optional

from .base import OCRPlugin


class PluginLoader:
    """
    外掛載入器

    負責發現、載入和管理外掛
    """

    def __init__(self, plugin_dir: str = "plugins", enable_plugins: bool = True):
        """
        初始化外掛載入器

        Args:
            plugin_dir: 外掛目錄路徑
            enable_plugins: 是否啟用外掛載入（安全性選項）
        """
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, OCRPlugin] = {}
        self.logger = logging.getLogger("PluginLoader")
        self.enable_plugins = enable_plugins
        
        # 安全性檢查：警告如果外掛目錄可寫
        if self.plugin_dir.exists():
            self._check_directory_permissions()

    def _check_directory_permissions(self) -> None:
        """
        檢查外掛目錄許可權（安全性）
        
        警告：如果外掛目錄對當前程序可寫，可能存在安全風險。
        """
        import os
        import stat
        
        try:
            # 檢查目錄是否可寫
            if os.access(self.plugin_dir, os.W_OK):
                self.logger.warning(
                    f"安全性警告：外掛目錄 {self.plugin_dir} 對當前程序可寫。"
                    "建議設定為唯讀以防止未授權的外掛上傳。"
                )
            
            # 檢查目錄許可權
            dir_stat = self.plugin_dir.stat()
            mode = stat.filemode(dir_stat.st_mode)
            self.logger.info(f"外掛目錄許可權: {mode}")
            
        except Exception as e:
            self.logger.debug(f"無法檢查外掛目錄許可權: {e}")

    def discover_plugins(self) -> List[str]:
        """
        發現外掛目錄中的所有外掛

        Returns:
            外掛檔案路徑列表
        """
        if not self.plugin_dir.exists():
            self.logger.warning(f"外掛目錄不存在: {self.plugin_dir}")
            return []

        plugin_files = []

        # 查詢所有.py檔案
        for py_file in self.plugin_dir.glob("*.py"):
            # 跳過__init__.py和以_開頭的檔案
            if py_file.name.startswith("_"):
                continue

            plugin_files.append(str(py_file))
            self.logger.debug(f"發現外掛檔案: {py_file.name}")

        return plugin_files

    def load_plugin_from_file(self, file_path: str) -> Optional[OCRPlugin]:
        """
        從檔案載入外掛

        Args:
            file_path: 外掛檔案路徑

        Returns:
            外掛例項，如果載入失敗則返回None
        """
        try:
            # 載入模組
            module_name = Path(file_path).stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)

            if spec is None or spec.loader is None:
                self.logger.error(f"無法載入外掛: {file_path}")
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查詢OCRPlugin的子類
            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                # 檢查是否為OCRPlugin子類（且不是OCRPlugin本身）
                if (
                    isinstance(attr, type)
                    and issubclass(attr, OCRPlugin)
                    and attr != OCRPlugin
                ):
                    # 例項化外掛
                    plugin = attr()

                    # 初始化外掛
                    if plugin.initialize():
                        self.logger.info(f"成功載入外掛: {plugin.name} v{plugin.version}")
                        return plugin
                    else:
                        self.logger.warning(f"外掛初始化失敗: {plugin.name}")
                        return None

            self.logger.warning(f"在 {file_path} 中未找到外掛類別")
            return None

        except Exception as e:
            self.logger.error(f"載入外掛時發生錯誤 {file_path}: {e}")
            return None

    def load_all_plugins(self) -> int:
        """
        載入所有發現的外掛

        Returns:
            成功載入的外掛數量
        """
        # 安全性：如果外掛被禁用，跳過載入
        if not self.enable_plugins:
            self.logger.info("外掛載入已禁用（安全性設定）")
            return 0
        
        plugin_files = self.discover_plugins()
        loaded_count = 0

        for file_path in plugin_files:
            plugin = self.load_plugin_from_file(file_path)

            if plugin:
                self.plugins[plugin.name] = plugin
                loaded_count += 1

        self.logger.info(f"已載入 {loaded_count}/{len(plugin_files)} 個外掛")
        return loaded_count

    def get_plugin(self, name: str) -> Optional[OCRPlugin]:
        """
        取得指定名稱的外掛

        Args:
            name: 外掛名稱

        Returns:
            外掛例項，如果不存在則返回None
        """
        return self.plugins.get(name)

    def get_all_plugins(self) -> Dict[str, OCRPlugin]:
        """取得所有已載入的外掛"""
        return self.plugins.copy()

    def enable_plugin(self, name: str) -> bool:
        """
        啟用外掛

        Args:
            name: 外掛名稱

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
        停用外掛

        Args:
            name: 外掛名稱

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
        解除安裝外掛

        Args:
            name: 外掛名稱

        Returns:
            是否成功解除安裝
        """
        plugin = self.plugins.pop(name, None)
        if plugin:
            plugin.on_shutdown()
            self.logger.info(f"已解除安裝外掛: {name}")
            return True
        return False

    def unload_all_plugins(self) -> None:
        """解除安裝所有外掛"""
        for plugin_name in list(self.plugins.keys()):
            self.unload_plugin(plugin_name)

    def get_plugin_info(self, name: str) -> Optional[Dict]:
        """取得外掛資訊"""
        plugin = self.get_plugin(name)
        return plugin.get_info() if plugin else None

    def list_plugins(self) -> List[Dict]:
        """列出所有外掛資訊"""
        return [plugin.get_info() for plugin in self.plugins.values()]


# 使用範例
if __name__ == "__main__":
    print("外掛載入器")
    print("\n使用方法:")
    print(
        """
from paddleocr_toolkit.plugins.loader import PluginLoader

# 建立載入器
loader = PluginLoader('plugins/')

# 載入所有外掛
loader.load_all_plugins()

# 列出外掛
for info in loader.list_plugins():
    print(f"- {info['name']} v{info['version']}")

# 使用外掛
plugin = loader.get_plugin('MyPlugin')
if plugin:
    processed = plugin.process_before_ocr(image)
"""
    )
