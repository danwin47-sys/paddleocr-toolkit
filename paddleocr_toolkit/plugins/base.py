#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件基類
v1.2.0新增 - 可擴展的插件系統
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging


class OCRPlugin(ABC):
    """
    OCR插件基類
    
    所有插件都應繼承此類並實作相關方法
    """
    
    # 插件元資料
    name: str = "Plugin Name"
    version: str = "1.0.0"
    author: str = "Author"
    description: str = "Plugin Description"
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化插件
        
        Args:
            config: 插件配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"plugin.{self.name}")
        self.enabled = True
        self._initialized = False
    
    @abstractmethod
    def on_init(self) -> bool:
        """
        插件初始化鉤子
        
        此方法在插件載入時調用
        
        Returns:
            是否初始化成功
        """
        pass
    
    @abstractmethod
    def on_before_ocr(self, image: Any) -> Any:
        """
        OCR前處理鉤子
        
        在OCR處理之前調用，可用於圖片預處理
        
        Args:
            image: 輸入圖片
        
        Returns:
            處理後的圖片
        """
        pass
    
    @abstractmethod
    def on_after_ocr(self, results: Any) -> Any:
        """
        OCR後處理鉤子
        
        在OCR處理之後調用，可用於結果後處理
        
        Args:
            results: OCR結果
        
        Returns:
            處理後的結果
        """
        pass
    
    def on_error(self, error: Exception) -> None:
        """
        錯誤處理鉤子
        
        當OCR處理發生錯誤時調用
        
        Args:
            error: 異常物件
        """
        self.logger.error(f"插件 {self.name} 發生錯誤: {error}")
    
    def on_shutdown(self) -> None:
        """
        插件關閉鉤子
        
        在插件卸載時調用，用於清理資源
        """
        self.logger.info(f"插件 {self.name} 正在關閉")
    
    def get_info(self) -> Dict[str, Any]:
        """
        取得插件資訊
        
        Returns:
            插件資訊字典
        """
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "enabled": self.enabled,
            "initialized": self._initialized
        }
    
    def enable(self) -> None:
        """啟用插件"""
        self.enabled = True
        self.logger.info(f"插件 {self.name} 已啟用")
    
    def disable(self) -> None:
        """停用插件"""
        self.enabled = False
        self.logger.info(f"插件 {self.name} 已停用")
    
    def initialize(self) -> bool:
        """
        初始化插件（內部使用）
        
        Returns:
            是否初始化成功
        """
        if self._initialized:
            return True
        
        try:
            success = self.on_init()
            self._initialized = success
            
            if success:
                self.logger.info(f"插件 {self.name} v{self.version} 初始化成功")
            else:
                self.logger.warning(f"插件 {self.name} 初始化失敗")
            
            return success
        except Exception as e:
            self.logger.error(f"插件 {self.name} 初始化時發生錯誤: {e}")
            return False
    
    def process_before_ocr(self, image: Any) -> Any:
        """
        執行OCR前處理（內部使用）
        
        Args:
            image: 輸入圖片
        
        Returns:
            處理後的圖片
        """
        if not self.enabled or not self._initialized:
            return image
        
        try:
            return self.on_before_ocr(image)
        except Exception as e:
            self.on_error(e)
            return image
    
    def process_after_ocr(self, results: Any) -> Any:
        """
        執行OCR後處理（內部使用）
        
        Args:
            results: OCR結果
        
        Returns:
            處理後的結果
        """
        if not self.enabled or not self._initialized:
            return results
        
        try:
            return self.on_after_ocr(results)
        except Exception as e:
            self.on_error(e)
            return results


class PreprocessorPlugin(OCRPlugin):
    """預處理插件基類"""
    
    def on_after_ocr(self, results: Any) -> Any:
        """預處理插件不處理OCR結果"""
        return results


class PostprocessorPlugin(OCRPlugin):
    """後處理插件基類"""
    
    def on_before_ocr(self, image: Any) -> Any:
        """後處理插件不處理輸入圖片"""
        return image


# 使用範例
if __name__ == "__main__":
    print("OCR插件基類")
    print("\n建立自訂插件:")
    print("""
class MyPlugin(OCRPlugin):
    name = "My Plugin"
    version = "1.0.0"
    
    def on_init(self):
        return True
    
    def on_before_ocr(self, image):
        # 處理圖片
        return image
    
    def on_after_ocr(self, results):
        # 處理結果
        return results
""")
