Add-Type -AssemblyName PresentationFramework

& shutdown /s /t 60 /c "TZG Dashboard updated! Auto shutdown in 60s. Click No to cancel."

$msg = "Dashboard updated and pushed!`n`n60 seconds until auto-shutdown.`n`n[Yes] Shutdown now`n[No]  Cancel shutdown"
$result = [System.Windows.MessageBox]::Show($msg, "TZG - Shutdown", [System.Windows.MessageBoxButton]::YesNo, [System.Windows.MessageBoxImage]::Question)

if ($result -eq "Yes") {
    & shutdown /s /t 0
} else {
    & shutdown /a
    [System.Windows.MessageBox]::Show("Auto-shutdown cancelled.", "TZG", [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::Information) | Out-Null
}
