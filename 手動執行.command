#!/usr/bin/env bash
# 雙擊這個檔案就會在 Terminal 跑一次 dashboard 流程（手動模式）
# 等同於：./主流程.sh
cd "$(dirname "$0")"
./主流程.sh
echo
echo "=== 完成。按 Enter 關閉視窗 ==="
read
