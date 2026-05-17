#!/usr/bin/env bash
# 雙擊這個檔案就會在 Terminal 跑一次 dashboard 流程（手動模式）
# 跑完自動關閉 Terminal 視窗（不用按 Enter）
cd "$(dirname "$0")"
./主流程.sh
echo
echo "=== 完成，1 分鐘後自動關閉視窗 ==="
sleep 60
# 關閉這個 Terminal 視窗
TTY_NAME="$(tty | sed 's|/dev/||')"
osascript -e "tell application \"Terminal\" to close (every window whose tty contains \"$TTY_NAME\")" &
exit 0
