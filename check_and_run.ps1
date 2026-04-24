# TZG Dashboard - 開機檢查腳本
# 如果過去 24 小時內沒有更新儀表板，詢問使用者是否要立即執行
# ─────────────────────────────────────────────────────

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Definition
$LatestHtml = Join-Path $ScriptDir "output\dashboard_latest.html"
$BatFile    = Join-Path $ScriptDir "generate_and_deploy.bat"

# 計算距離上次更新幾小時
$HoursSince  = 99   # 預設：很久沒更新
$LastUpdated = "（尚未產生）"

if (Test-Path $LatestHtml) {
    $LastWriteTime = (Get-Item $LatestHtml).LastWriteTime
    $HoursSince    = ((Get-Date) - $LastWriteTime).TotalHours
    $LastUpdated   = $LastWriteTime.ToString("yyyy-MM-dd HH:mm")
}

# 24 小時內有更新過 → 靜默退出，不打擾
if ($HoursSince -lt 24) {
    exit 0
}

# ── 超過 24 小時沒更新，顯示提示 ──────────────────────
Add-Type -AssemblyName PresentationFramework

$Hours   = [math]::Round($HoursSince, 0)
$Message = "📊 TZG 儀表板已超過 $Hours 小時未更新

上次更新：$LastUpdated

要現在執行更新嗎？
（下載 Shopline 資料 → 計算 KPI → 上傳）"

$Result = [System.Windows.MessageBox]::Show(
    $Message,
    "TZG 電商儀表板",
    [System.Windows.MessageBoxButton]::YesNo,
    [System.Windows.MessageBoxImage]::Question
)

if ($Result -eq "Yes") {
    Start-Process "cmd.exe" `
        -ArgumentList "/c `"$BatFile`"" `
        -WorkingDirectory $ScriptDir
}
