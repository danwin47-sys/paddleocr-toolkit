# -*- coding: utf-8 -*-
"""
設定檔載入器

載入 YAML 設定檔，支援預設值和命令列參數覆蓋。
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# 預設設定
DEFAULT_CONFIG = {
    'ocr': {
        'mode': 'hybrid',
        'device': 'cpu',
        'dpi': 150,
        'orientation_classify': False,
        'unwarping': False,
    },
    'output': {
        'searchable': True,
        'all_formats': False,
        'show_progress': True,
        'debug_text': False,
    },
    'compression': {
        'enabled': True,
        'jpeg_quality': 85,
    },
    'translation': {
        'enabled': False,
        'source_lang': 'auto',
        'target_lang': 'en',
        'ollama_model': 'qwen2.5:7b',
        'ollama_url': 'http://localhost:11434',
        'mono_pdf': True,
        'dual_pdf': True,
        'dual_mode': 'alternating',
        'ocr_workaround': False,
    },
}


def deep_merge(base: Dict, override: Dict) -> Dict:
    """
    深度合併兩個字典，override 會覆蓋 base 中的值
    
    Args:
        base: 基礎字典
        override: 覆蓋字典
        
    Returns:
        合併後的字典
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    載入設定檔
    
    搜尋順序：
    1. 指定的路徑
    2. 當前目錄的 config.yaml
    3. 使用者目錄的 ~/.paddleocr_toolkit/config.yaml
    4. 預設設定
    
    Args:
        config_path: 設定檔路徑（可選）
        
    Returns:
        設定字典
    """
    config = DEFAULT_CONFIG.copy()
    
    if not HAS_YAML:
        logging.warning("PyYAML 未安裝，使用預設設定")
        return config
    
    # 搜尋設定檔
    search_paths = []
    
    if config_path:
        search_paths.append(Path(config_path))
    
    search_paths.extend([
        Path.cwd() / 'config.yaml',
        Path.cwd() / 'config.yml',
        Path.home() / '.paddleocr_toolkit' / 'config.yaml',
    ])
    
    # 嘗試載入
    for path in search_paths:
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
                
                if file_config:
                    config = deep_merge(config, file_config)
                    logging.info(f"已載入設定檔: {path}")
                    return config
                    
            except Exception as e:
                logging.warning(f"載入設定檔失敗 ({path}): {e}")
    
    logging.debug("使用預設設定")
    return config


def apply_config_to_args(config: Dict[str, Any], args) -> None:
    """
    將設定檔的值套用到 argparse 參數（作為預設值）
    
    命令列參數優先於設定檔。
    
    Args:
        config: 設定字典
        args: argparse.Namespace 物件
    """
    # OCR 設定
    ocr = config.get('ocr', {})
    if not hasattr(args, '_explicit_mode'):
        args.mode = args.mode or ocr.get('mode', 'hybrid')
    if not hasattr(args, '_explicit_device'):
        args.device = args.device or ocr.get('device', 'cpu')
    if not hasattr(args, '_explicit_dpi'):
        args.dpi = args.dpi or ocr.get('dpi', 150)
    
    # 輸出設定
    output = config.get('output', {})
    if not args.no_progress:
        args.no_progress = not output.get('show_progress', True)
    
    # 壓縮設定
    compression = config.get('compression', {})
    if not hasattr(args, '_explicit_compress'):
        args.no_compress = not compression.get('enabled', True)
    if not hasattr(args, '_explicit_quality'):
        args.jpeg_quality = args.jpeg_quality or compression.get('jpeg_quality', 85)
    
    # 翻譯設定
    translation = config.get('translation', {})
    if hasattr(args, 'translate') and not args.translate:
        args.translate = translation.get('enabled', False)
    if hasattr(args, 'source_lang'):
        args.source_lang = args.source_lang or translation.get('source_lang', 'auto')
    if hasattr(args, 'target_lang'):
        args.target_lang = args.target_lang or translation.get('target_lang', 'en')
    if hasattr(args, 'ollama_model'):
        args.ollama_model = args.ollama_model or translation.get('ollama_model', 'qwen2.5:7b')
    if hasattr(args, 'ollama_url'):
        args.ollama_url = args.ollama_url or translation.get('ollama_url', 'http://localhost:11434')


def get_config_value(config: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    取得巢狀設定值
    
    Args:
        config: 設定字典
        path: 點分隔的路徑，如 'ocr.mode'
        default: 預設值
        
    Returns:
        設定值
        
    Example:
        >>> get_config_value(config, 'translation.ollama_model')
        'qwen2.5:7b'
    """
    keys = path.split('.')
    value = config
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value


def save_config(config: Dict[str, Any], config_path: str) -> bool:
    """
    儲存設定檔
    
    Args:
        config: 設定字典
        config_path: 儲存路徑
        
    Returns:
        是否成功
    """
    if not HAS_YAML:
        logging.error("PyYAML 未安裝，無法儲存設定檔")
        return False
    
    try:
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        logging.info(f"設定檔已儲存: {path}")
        return True
        
    except Exception as e:
        logging.error(f"儲存設定檔失敗: {e}")
        return False
