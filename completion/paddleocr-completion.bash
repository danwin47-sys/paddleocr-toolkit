#!/usr/bin/env bash
# PaddleOCR Toolkit Bash 自動補全腳本

_paddleocr_completions()
{
    local cur prev opts base
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # 主要命令
    local commands="init config process benchmark validate --version --help"
    
    # 如果是第一個參數，補全命令
    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
        return 0
    fi
    
    # 根據不同命令補全選項
    case "${prev}" in
        init)
            # init命令後補全目錄
            COMPREPLY=( $(compgen -d -- ${cur}) )
            return 0
            ;;
        config)
            COMPREPLY=( $(compgen -W "--show" -- ${cur}) )
            return 0
            ;;
        process)
            # process命令選項
            local process_opts="--mode --output --format"
            COMPREPLY=( $(compgen -W "${process_opts}" -- ${cur}) )
            # 也補全檔案
            COMPREPLY+=( $(compgen -f -- ${cur}) )
            return 0
            ;;
        --mode)
            COMPREPLY=( $(compgen -W "basic hybrid structure" -- ${cur}) )
            return 0
            ;;
        --format)
            COMPREPLY=( $(compgen -W "md json html txt xlsx" -- ${cur}) )
            return 0
            ;;
        benchmark)
            # 補全PDF檔案
            COMPREPLY=( $(compgen -f -X '!*.pdf' -- ${cur}) )
            COMPREPLY+=( $(compgen -W "--output" -- ${cur}) )
            return 0
            ;;
        validate)
            # 補全JSON和TXT檔案
            COMPREPLY=( $(compgen -f -X '!*.json' -- ${cur}) )
            COMPREPLY+=( $(compgen -f -X '!*.txt' -- ${cur}) )
            return 0
            ;;
        *)
            ;;
    esac
    
    # 預設補全檔案
    COMPREPLY=( $(compgen -f -- ${cur}) )
    return 0
}

# 註冊補全函數
complete -F _paddleocr_completions paddleocr

# 使用說明：
# 將此檔案複製到 /etc/bash_completion.d/ 或
# 在 ~/.bashrc 中加入：
# source /path/to/paddleocr-completion.bash
