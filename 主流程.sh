#!/usr/bin/env bash
# TZG Dashboard Generator + Auto Deploy (macOS)
# 用法：
#   ./generate_and_deploy.sh             手動：只抓當月，瀏覽器看得見
#   ./generate_and_deploy.sh --auto      排程白天：抓上月 1 號~今天，headless，不睡眠
#   ./generate_and_deploy.sh --shutdown  排程晚上：抓上月 1 號~今天，headless，跑完睡眠
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON="${TZG_PYTHON:-python3}"
MODE="${1:-}"

mkdir -p logs

# 這次執行發現的問題，最後統一寫診斷檔 + 發一次通知（不重試、只回報）
PROBLEMS=()

# 送 macOS 通知（處理特殊字元跳脫，訊息壓成一行）
notify() {
    local title="$1" msg="$2"
    local esc_title esc_msg
    esc_title="$(printf '%s' "$title" | sed 's/\\/\\\\/g; s/"/\\"/g')"
    esc_msg="$(printf '%s' "$msg" | sed 's/\\/\\\\/g; s/"/\\"/g' | tr '\n' ' ')"
    osascript -e "display notification \"$esc_msg\" with title \"$esc_title\" sound name \"Sosumi\"" 2>/dev/null || true
}

echo
echo "==================================================="
echo " TZG Dashboard Generator + Auto Deploy"
echo "==================================================="
echo

# ============ Step 1: Python check ============
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "ERROR: $PYTHON not found! 請先安裝 Python 3。"
    exit 1
fi
echo "[1/6] Python OK ($($PYTHON --version))"

# ============ Step 2: data folder check ============
if [ ! -d "data" ]; then
    echo "ERROR: data directory not found!"
    exit 1
fi
echo "[2/6] data directory OK"

# ============ Step 3: script check ============
if [ ! -f "generate_daily.py" ]; then
    echo "ERROR: generate_daily.py not found!"
    exit 1
fi
echo "[3/6] generate_daily.py OK"

# ============ Step 4: Git check ============
if ! command -v git >/dev/null 2>&1; then
    echo "ERROR: Git not found!"
    exit 1
fi
echo "[4/6] Git OK"
echo

# 自動拉取最新版本（讓本機端的開發改動先同步進來，避免之後 push 衝突）
echo "==================================================="
echo " Pulling latest from GitHub..."
echo "==================================================="
if git pull --rebase --autostash origin main; then
    echo "[4b/6] Git pull OK"
else
    echo "WARNING: git pull 失敗，繼續用本地版本跑（之後 push 可能衝突）"
fi
echo

# ============ Step 5a: Auto Download from Shopline ============
if [ -f ".env" ]; then
    TODAY="$(date +%Y-%m-%d)"
    # 算各種日期（macOS BSD date）
    LASTMONTH_START="$(date -v-1m -v1d +%Y-%m-%d)"           # 上月 1 號
    LASTMONTH_END="$(date -v1d -v-1d +%Y-%m-%d)"             # 上月最後一天（本月 1 號 - 1）
    THISMONTH_START="$(date -v1d +%Y-%m-%d)"                 # 本月 1 號
    LASTMONTH="$(date -v-1m +%Y-%m)"

    if [ "$MODE" = "--shutdown" ] || [ "$MODE" = "--auto" ]; then
        echo "==================================================="
        echo " Downloading from Shopline (split: last month + this month)"
        echo "   Range A (上月): $LASTMONTH_START ~ $LASTMONTH_END"
        echo "   Range B (本月): $THISMONTH_START ~ $TODAY"
        echo "==================================================="
        echo "  ※ 拆兩段抓：Shopline 報表跨月查詢常漏抓本月即時訂單，"
        echo "    分開抓比較能拿到本月新單。"
        echo

        echo "--- [A] 抓上月整月 ---"
        TZG_HEADLESS=1 "$PYTHON" auto_shopline.py --start "$LASTMONTH_START" --end "$LASTMONTH_END"
        rc_a=$?

        echo
        echo "--- [B] 抓本月至今 ---"
        TZG_HEADLESS=1 "$PYTHON" auto_shopline.py --start "$THISMONTH_START" --end "$TODAY"
        rc_b=$?

        if [ $rc_a -ne 0 ] && [ $rc_b -ne 0 ]; then
            echo "WARNING: Shopline 兩段下載都失敗（A=$rc_a, B=$rc_b）。沿用既有資料..."
            PROBLEMS+=("Shopline 下載完全失敗（上月+本月，錯誤碼 A=$rc_a B=$rc_b），本次用舊資料產生報表")
            echo
        else
            if [ $rc_a -ne 0 ]; then
                echo "WARNING: 上月下載失敗（A=$rc_a），但本月成功。"
                PROBLEMS+=("上月資料下載失敗（錯誤碼 $rc_a），沿用舊的上月資料")
            fi
            if [ $rc_b -ne 0 ]; then
                echo "WARNING: 本月下載失敗（B=$rc_b），但上月成功。"
                PROBLEMS+=("本月資料下載失敗（錯誤碼 $rc_b），沿用舊的本月資料 ← 通常是資料停滯的主因")
            fi
            echo "[5a] Shopline download OK"
            echo
            echo " Rebuilding last-month archive ($LASTMONTH)..."
            "$PYTHON" generate_monthly_archive.py --month "$LASTMONTH" --force \
                || echo "WARNING: Last-month archive rebuild failed, continuing..."
            echo
            echo " Cleanup old downloads..."
            "$PYTHON" cleanup_old_downloads.py
            echo
        fi
    else
        echo "==================================================="
        echo " Downloading from Shopline (current month, manual)"
        echo "==================================================="
        echo
        "$PYTHON" auto_shopline.py
        rc_manual=$?
        if [ $rc_manual -ne 0 ]; then
            echo "WARNING: Shopline download failed. Continuing with existing data..."
            PROBLEMS+=("Shopline 下載失敗（錯誤碼 $rc_manual），沿用舊資料")
            echo
        else
            echo "[5a] Shopline download OK"
            echo
        fi
    fi
else
    echo "[5a] .env not found, skipping auto-download"
    echo "     To enable: cp .env.example .env and fill in credentials"
    echo
fi

# ============ Step 5: Generate Dashboard ============
echo "==================================================="
echo " Generating Dashboard..."
echo "==================================================="
echo

DAILY_LOG="logs/generate_daily_last.log"
PYTHONUNBUFFERED=1 "$PYTHON" generate_daily.py 2>&1 | tee "$DAILY_LOG"
DAILY_RC=${PIPESTATUS[0]}

if [ "$DAILY_RC" -ne 0 ]; then
    echo
    echo "ERROR: Dashboard generation failed!"
    notify "❌ TZG Dashboard 產生失敗" "generate_daily.py 整個執行失敗（錯誤碼 $DAILY_RC），詳見 logs/generate_daily_last.log"
    exit 1
fi
echo
echo "[5/6] Dashboard generated OK"
echo

# 資料檔案讀取失敗檢查（某份 .xls/.csv 被靜靜跳過，不會讓上面整體失敗，
# 但長期下來 dashboard 會卡在舊資料 → 不用等 24h 停滯，這次執行馬上回報）
FAIL_LINES="$(grep -E '^[[:space:]]*\[X\]' "$DAILY_LOG" 2>/dev/null || true)"
if [ -n "$FAIL_LINES" ]; then
    N_FAIL=$(printf '%s\n' "$FAIL_LINES" | grep -c '^')
    PROBLEMS+=("有 $N_FAIL 個資料檔案讀取失敗（今晚的資料可能不完整，詳見 logs/generate_daily_last.log）")
fi

# 資料新鮮度檢查（最新訂單日期距今 > 24h → 可能 session 過期或下載沒抓到新單）
STALE_HOURS=$("$PYTHON" -c "
import re
from datetime import datetime
try:
    html = open('output/dashboard_latest.html', encoding='utf-8').read()
    m = re.search(r'\"data_as_of\":\s*\"([^\"]+)\"', html)
    if m:
        d = datetime.strptime(m.group(1), '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        print(int(max(0, (datetime.now() - d).total_seconds() / 3600)))
    else:
        print(0)
except Exception:
    print(0)
" 2>/dev/null || echo "0")

if [ "$STALE_HOURS" -gt 24 ]; then
    PROBLEMS+=("資料停滯 $STALE_HOURS 小時，最新訂單不是今天/昨天，Shopline 可能 session 過期")
fi
echo

# ============ 若本次執行有任何問題：寫診斷檔 + 立刻通知一次 ============
# 只回報，不重試 —— 不確定原因時不要自己再重跑，寫清楚讓人來看。
# 沒問題就清掉舊診斷檔，避免昨天的問題殘留誤導（檔案存在 = 現在有問題）。
if [ ${#PROBLEMS[@]} -eq 0 ]; then
    rm -f logs/last_diagnosis.txt
else
    {
        echo "=== TZG Dashboard 執行診斷 $(date '+%Y-%m-%d %H:%M:%S') ==="
        echo
        for p in "${PROBLEMS[@]}"; do
            echo "• $p"
        done
        if [ -n "$FAIL_LINES" ]; then
            echo
            echo "--- 檔案讀取失敗詳情 ---"
            printf '%s\n' "$FAIL_LINES"
        fi
    } > logs/last_diagnosis.txt

    echo "⚠️  本次執行有 ${#PROBLEMS[@]} 個問題，已寫入 logs/last_diagnosis.txt 並發送通知"
    SUMMARY="${PROBLEMS[0]}"
    if [ ${#PROBLEMS[@]} -gt 1 ]; then
        SUMMARY="$SUMMARY（+$((${#PROBLEMS[@]} - 1)) 項問題，詳見 logs/last_diagnosis.txt）"
    fi
    notify "⚠️ TZG Dashboard 執行異常" "$SUMMARY"
    echo
fi

# ============ Step 5b: Generate Monthly Review ============
echo "==================================================="
echo " Generating Monthly Review..."
echo "==================================================="
echo
if ! "$PYTHON" generate_monthly_review.py; then
    echo "WARNING: Monthly review generation failed, continuing..."
    echo
else
    echo "[5b/6] Monthly review generated OK"
    echo
fi

# ============ Step 6: Git commit + push ============
echo "==================================================="
echo " Deploying to GitHub..."
echo "==================================================="
echo

if [ ! -d ".git" ]; then
    echo "ERROR: This folder is not a Git repository!"
    exit 1
fi

TIMESTAMP="$(date +'%Y-%m-%d %H:%M')"

git add output/dashboard_latest.html
[ -f "output/monthly_review.html" ] && git add output/monthly_review.html

if git diff --cached --quiet; then
    echo "No changes to deploy. Dashboard content is identical."
    echo
else
    if ! git commit -m "Update dashboard $TIMESTAMP"; then
        echo "ERROR: Git commit failed!"
        notify "❌ TZG Dashboard 部署失敗" "git commit 失敗，dashboard 沒有推上 GitHub"
        exit 1
    fi
    if ! git push origin main; then
        echo "ERROR: Git push failed!"
        echo "Possible reasons: 未登入 GitHub / 網路 / 分支衝突"
        notify "❌ TZG Dashboard 部署失敗" "git push 失敗（可能是網路或分支衝突），dashboard 沒有推上 GitHub"
        exit 1
    fi
    echo
    echo "[6/6] Deployed to GitHub OK"
    echo
fi

echo "==================================================="
echo " SUCCESS! All done."
echo "==================================================="
echo
echo "Your dashboard is now live on GitHub Pages."
echo "It may take 1-2 minutes for the new version to appear."
echo

# 手動模式：開啟本機 preview（排程模式不開）
if [ -z "$MODE" ] && [ -f "output/dashboard_latest.html" ]; then
    echo "Opening local preview..."
    open "output/dashboard_latest.html"
fi
# 註：23:59 排程跑完後的關機由 pmset repeat shutdown 排定（00:10），不在此腳本處理
