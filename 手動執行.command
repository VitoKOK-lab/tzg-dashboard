#!/usr/bin/env bash
# 雙擊這個檔案就會在 Terminal 跑一次 dashboard 流程（手動模式）
# 等同於：./generate_and_deploy.sh
cd "$(dirname "$0")"
./generate_and_deploy.sh
echo
echo "=== 完成。按 Enter 關閉視窗 ==="
read
