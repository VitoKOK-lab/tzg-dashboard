#!/usr/bin/env bash
# 開機/登入時自動跑：檢查今天有沒有跑過，沒有就補跑。
# 由 com.tzg.dashboard.boot.plist (RunAtLoad=true) 觸發。
set -u
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

LATEST="output/dashboard_latest.html"

# 排程只剩每天 23:59 一次,所以改看「距離上次更新幾小時」:
# 不能用「今天跑過沒」,否則昨晚 23:59 跑完、隔天早上開機又會補跑一次
if [ -f "$LATEST" ]; then
    AGE_H=$(( ( $(date +%s) - $(stat -f %m "$LATEST") ) / 3600 ))
else
    AGE_H=9999
fi

echo "[catchup] 上次更新：$AGE_H 小時前"

if [ "$AGE_H" -lt 24 ]; then
    echo "[catchup] 24 小時內已更新過，略過。"
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
exec ./主流程.sh --auto
