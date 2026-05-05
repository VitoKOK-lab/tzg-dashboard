#!/usr/bin/env bash
set -u
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON="${TZG_PYTHON:-python3}"
export PYTHONIOENCODING=utf-8

if ! "$PYTHON" edit_targets.py; then
    echo
    echo "[!] 執行時發生錯誤"
    read -n 1 -s -r -p "按任意鍵關閉..."
    echo
fi
