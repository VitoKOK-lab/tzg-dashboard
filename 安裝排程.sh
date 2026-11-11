#!/usr/bin/env bash
# 安裝 / 重裝 macOS 排程:每天 23:59 同步一次 + 開機登入時補跑
# 排程檔用「這支腳本所在的資料夾」當專案路徑自動產生,換電腦、換帳號都直接重跑這支就好。
#
# 用法:  ./安裝排程.sh
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
LA="$HOME/Library/LaunchAgents"
mkdir -p "$LA"
chmod +x "$DIR/主流程.sh" "$DIR/開機補跑.sh"

# 舊排程(含已停用的 15:00 afternoon)先卸載、刪除
for label in com.tzg.dashboard.daily com.tzg.dashboard.boot com.tzg.dashboard.afternoon; do
    if [ -f "$LA/$label.plist" ]; then
        launchctl unload "$LA/$label.plist" 2>/dev/null || true
        rm -f "$LA/$label.plist"
    fi
done

cat > "$LA/com.tzg.dashboard.daily.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tzg.dashboard.daily</string>
    <key>ProgramArguments</key>
    <array>
        <string>$DIR/主流程.sh</string>
        <string>--shutdown</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$DIR</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>23</integer>
        <key>Minute</key>
        <integer>59</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/tzg_dashboard.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/tzg_dashboard.err</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

cat > "$LA/com.tzg.dashboard.boot.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tzg.dashboard.boot</string>
    <key>ProgramArguments</key>
    <array>
        <string>$DIR/開機補跑.sh</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/tzg_dashboard_boot.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/tzg_dashboard_boot.err</string>
</dict>
</plist>
EOF

launchctl load "$LA/com.tzg.dashboard.daily.plist"
launchctl load "$LA/com.tzg.dashboard.boot.plist"

echo "[✓] 排程已安裝,專案路徑:$DIR"
echo "    每天 23:59 同步一次;開機登入時若超過 24 小時沒更新會自動補跑"
echo
launchctl list | grep tzg || true
