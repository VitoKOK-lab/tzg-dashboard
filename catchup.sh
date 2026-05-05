#!/usr/bin/env bash
# 開機/登入時自動跑：檢查今天有沒有跑過，沒有就補跑。
# 由 com.tzg.dashboard.boot.plist (RunAtLoad=true) 觸發。
set -u
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

LATEST="output/dashboard_latest.html"
TODAY="$(date +%Y-%m-%d)"

if [ -f "$LATEST" ]; then
    LAST_DAY="$(stat -f %Sm -t %Y-%m-%d "$LATEST")"
else
    LAST_DAY="1970-01-01"
fi

echo "[catchup] 今日：$TODAY / 上次更新：$LAST_DAY"

if [ "$LAST_DAY" = "$TODAY" ]; then
    echo "[catchup] 今天已執行過，略過。"
    exit 0
fi

# 等網路（Wi-Fi 重連通常 < 30 秒）
echo "[catchup] 等待網路連線..."
for i in $(seq 1 30); do
    if ping -c 1 -W 2000 1.1.1.1 >/dev/null 2>&1; then
        echo "[catchup] 網路 OK（嘗試 $i 次）"
        break
    fi
    sleep 2
done

echo "[catchup] 開始補跑..."
exec ./generate_and_deploy.sh --auto
