#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動簡繁轉換工具
使用 OpenCC 將專案中的簡體中文轉換為繁體中文（臺灣習慣與用語修正）。
"""

import os
import sys
from pathlib import Path
import argparse

try:
    from opencc import OpenCC
except ImportError:
    print("錯誤: 找不到 OpenCC 模組。")
    print("請執行: pip install opencc-python-reimplemented")
    sys.exit(1)

# 支援的檔案型別
SUPPORTED_EXTENSIONS = {'.py', '.md', '.txt', '.html', '.css', '.yml', '.yaml', '.json', '.sql'}

# 排除的目錄
EXCLUDE_DIRS = {'.git', 'venv', '.venv', '__pycache__', 'node_modules', 'dist', 'build', '.pytest_cache'}

def localize_file(file_path: Path, config: str = 's2twp'):
    """轉換單個檔案"""
    cc = OpenCC(config)
    
    try:
        # 讀取內容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 進行轉換
        # s2twp: Simplified Chinese to Traditional Chinese (Taiwan Standard) with phrase conversion
        converted = cc.convert(content)
        
        if content == converted:
            return False # 無變更
            
        # 寫回內容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(converted)
        
        return True
    except UnicodeDecodeError:
        print(f"跳過非 UTF-8 檔案: {file_path}")
    except Exception as e:
        print(f"處理 {file_path} 時發生錯誤: {e}")
    
    return False

def main():
    parser = argparse.ArgumentParser(description="自動簡繁轉換工具 (OpenCC)")
    parser.add_argument("path", nargs="?", default=".", help="要轉換的目錄或檔案路徑 (預設為當前目錄)")
    parser.add_argument("--config", default="s2twp", help="OpenCC 配置 (預設: s2twp - 簡體轉臺灣繁體具用語修正)")
    parser.add_argument("--ext", help="限制特定的副檔名 (例如: .py,.md)")
    parser.add_argument("--dry-run", action="store_true", help="僅顯示將被轉換的檔案，不實際寫入")
    
    args = parser.parse_args()
    
    root_path = Path(args.path).resolve()
    extensions = set(args.ext.split(',')) if args.ext else SUPPORTED_EXTENSIONS
    
    print(f"開始掃描: {root_path}")
    print(f"使用配置: {args.config}")
    
    change_count = 0
    file_count = 0
    
    if root_path.is_file():
        files_to_process = [root_path]
    else:
        files_to_process = []
        for root, dirs, files in os.walk(root_path):
            # 過濾排除目錄
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in extensions:
                    files_to_process.append(file_path)

    for file_path in files_to_process:
        file_count += 1
        rel_path = file_path.relative_to(root_path) if root_path.is_dir() else file_path.name
        
        if args.dry_run:
            print(f"[待轉換] {rel_path}")
            change_count += 1
            continue
            
        if localize_file(file_path, args.config):
            print(f"[已轉換] {rel_path}")
            change_count += 1

    print("-" * 40)
    print(f"掃描結束。")
    print(f"掃描檔案總數: {file_count}")
    print(f"實際轉換數量: {change_count}")
    
    if args.dry_run:
        print("注意: 目前為測試模式，未實際修改檔案。")

if __name__ == "__main__":
    main()
