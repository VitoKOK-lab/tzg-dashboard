#!/usr/bin/env bash
# 排程模式跑完後跳對話框：60 秒倒數，按 Yes 立刻睡眠、按 No 取消。
# 用 pmset sleepnow（不需 sudo）。
set -u

ANSWER=$(osascript <<'EOF' 2>/dev/null
tell application "System Events"
    activate
    set theDialog to display dialog ¬
        "Dashboard updated and pushed!" & return & return & ¬
        "60 秒後自動進入睡眠。" & return & return & ¬
        "[Yes] 立刻睡眠   [No] 取消" ¬
        with title "TZG - Sleep" ¬
        buttons {"No", "Yes"} default button "Yes" ¬
        giving up after 60
    try
        button returned of theDialog
    on error
        "GaveUp"
    end try
end tell
EOF
)

case "$ANSWER" in
    "No")
        osascript -e 'display notification "已取消睡眠" with title "TZG"'
        ;;
    "Yes"|"GaveUp"|"")
        pmset sleepnow
        ;;
esac
