#!/usr/bin/env bash
# 檢查 dashboard_latest.html 是否超過 24 小時沒更新；超過就跳對話框問是否執行。
set -u
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

LATEST="$SCRIPT_DIR/output/dashboard_latest.html"
SH="$SCRIPT_DIR/generate_and_deploy.sh"

if [ -f "$LATEST" ]; then
    NOW=$(date +%s)
    MTIME=$(stat -f %m "$LATEST")
    DIFF=$(( (NOW - MTIME) / 3600 ))
    LAST_UPDATED=$(date -r "$MTIME" +'%Y-%m-%d %H:%M')
else
    DIFF=99
    LAST_UPDATED="(not generated yet)"
fi

# 24 小時內 → 安靜離開
if [ "$DIFF" -lt 24 ]; then
    exit 0
fi

# 用 osascript 跳 Yes/No 對話框
ANSWER=$(osascript <<EOF
tell application "System Events"
    activate
    set theDialog to display dialog ¬
        "TZG Dashboard 已 ${DIFF} 小時沒更新。" & return & return & ¬
        "上次更新：${LAST_UPDATED}" & return & return & ¬
        "現在執行更新嗎？" & return & ¬
        "(下載 Shopline 資料、計算 KPI、上傳)" ¬
        with title "TZG Dashboard" buttons {"No", "Yes"} default button "Yes"
    button returned of theDialog
end tell
EOF
)

if [ "$ANSWER" = "Yes" ]; then
    # 用 Terminal 開新視窗執行（看得到輸出）
    osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR' && ./generate_and_deploy.sh\""
fi
