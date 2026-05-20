#!/usr/bin/env bash
# 雙擊這個檔案就會在 Terminal 跑一次 dashboard 流程（手動模式）
# 跑完後自動關閉 Terminal 視窗，不再等 Enter、不再 sleep
cd "$(dirname "$0")"
./主流程.sh
RC=$?

# 用當前 tty 鎖定要關的視窗，避免誤關其他 Terminal 視窗
MY_TTY="$(tty)"
(
  sleep 0.3
  osascript >/dev/null 2>&1 <<APPLESCRIPT
tell application "Terminal"
    repeat with w in windows
        try
            if tty of selected tab of w is "$MY_TTY" then
                close w
                exit repeat
            end if
        end try
    end repeat
end tell
APPLESCRIPT
) &

exit $RC
