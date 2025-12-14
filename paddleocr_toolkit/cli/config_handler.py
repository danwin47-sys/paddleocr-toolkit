# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 設定檔處理器

處理設定檔載入和與 CLI 參數的合併。
"""

import argparse
import logging
from typing import Dict, Any, Optional
from pathlib import Path


def load_and_merge_config(
    cli_args: argparse.Namespace,
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """載入設定檔並與 CLI 參數合併
    
    Args:
        cli_args: argparse.Namespace 物件（CLI 參數）
        config_path: 設定檔路徑（可選，暫未實作）
    
    Returns:
        Dict[str, Any]: 合併後的設定字典
    
    Note:
        目前版本直接使用 CLI 參數，未來可擴展支援 YAML/JSON 設定檔。
    """
    # 將 Namespace 轉換為字典
    config = vars(cli_args).copy()
    
    # 未來可在此處載入設定檔並合併
    # if config_path and Path(config_path).exists():
    #     file_config = load_config_file(config_path)
    #     config.update(file_config)
    
    return config


def load_config_file(config_path: str) -> Dict[str, Any]:
    """從檔案載入設定（預留功能）
    
    Args:
        config_path: 設定檔路徑
    
    Returns:
        Dict[str, Any]: 設定字典
    """
    # 預留給未來的設定檔支援
    # 可支援 YAML 或 JSON 格式
    logging.warning(f"設定檔支援尚未實作: {config_path}")
    return {}


def process_args_overrides(args: argparse.Namespace) -> argparse.Namespace:
    """處理 CLI 參數的覆蓋邏輯
    
    包含：
    1. 處理 --no-* 選項覆蓋
    2. 處理 --all 參數啟用所有輸出
    
    Args:
        args: 命令列參數
    
    Returns:
        argparse.Namespace: 處理後的參數
    """
    # 處理 --no-* 選項來覆蓋預設值
    args = _process_no_flags(args)
    
    # 處理 --all 參數：一次啟用所有輸出格式
    args = _process_all_flag(args)
    
    return args


def _process_no_flags(args: argparse.Namespace) -> argparse.Namespace:
    """處理 --no-* 覆蓋選項
    
    Args:
        args: 命令列參數
    
    Returns:
        argparse.Namespace: 處理後的參數
    """
    if args.no_searchable:
        args.searchable = False
    if args.no_text_output:
        args.text_output = None
    if args.no_markdown_output:
        args.markdown_output = None
    if args.no_json_output:
        args.json_output = None
    
    return args


def _process_all_flag(args: argparse.Namespace) -> argparse.Namespace:
    """處理 --all 參數
    
    Args:
        args: 命令列參數
    
    Returns:
        argparse.Namespace: 處理後的參數
    """
    if hasattr(args, 'all') and args.all:
        if args.mode in ['structure', 'vl', 'hybrid']:
            args.markdown_output = args.markdown_output or 'AUTO'
            args.json_output = args.json_output or 'AUTO'
            args.html_output = args.html_output or 'AUTO'
            print(f"[--all] 啟用所有輸出格式：Markdown, JSON, HTML")
    
    return args

