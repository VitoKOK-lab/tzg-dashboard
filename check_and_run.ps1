Add-Type -AssemblyName PresentationFramework

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Definition
$LatestHtml = Join-Path $ScriptDir "output\dashboard_latest.html"
$BatFile    = Join-Path $ScriptDir "generate_and_deploy.bat"

# Check hours since last update
$HoursSince  = 99
$LastUpdated = "(not generated yet)"

if (Test-Path $LatestHtml) {
    $LastWriteTime = (Get-Item $LatestHtml).LastWriteTime
    $HoursSince    = ((Get-Date) - $LastWriteTime).TotalHours
    $LastUpdated   = $LastWriteTime.ToString("yyyy-MM-dd HH:mm")
}

# Updated within last 24 hours -> exit silently
if ($HoursSince -lt 24) {
    exit 0
}

# More than 24 hours -> show prompt
$Hours  = [math]::Round($HoursSince, 0)
$msg    = "TZG Dashboard has not been updated for $Hours hours.`n`nLast update: $LastUpdated`n`nRun update now?`n(Download Shopline data, calculate KPIs, upload)"
$result = [System.Windows.MessageBox]::Show($msg, "TZG Dashboard", [System.Windows.MessageBoxButton]::YesNo, [System.Windows.MessageBoxImage]::Question)

if ($result -eq "Yes") {
    Start-Process "cmd.exe" -ArgumentList "/c `"$BatFile`"" -WorkingDirectory $ScriptDir
}
