# TZG Dashboard - 完成後關機確認
# 安排 60 秒後自動關機，同時顯示對話框
# [是] 立即關機 / [否] 取消關機 / 無回應 → 60 秒後自動關機
# ─────────────────────────────────────────────────────

Add-Type -AssemblyName PresentationFramework

# 先排定 60 秒後關機，並在工作列顯示系統倒數通知
& shutdown /s /t 60 /c "TZG 儀表板已更新完成！60 秒後自動關機。如需取消請在對話框點「否」。"

# 顯示對話框
$Message = "✅ 儀表板已更新完成並上傳！

60 秒後將自動關機。

[是] 立即關機
[否] 取消關機，繼續使用電腦"

$Result = [System.Windows.MessageBox]::Show(
    $Message,
    "TZG 電商 — 關機確認",
    [System.Windows.MessageBoxButton]::YesNo,
    [System.Windows.MessageBoxImage]::Question
)

if ($Result -eq "Yes") {
    # 使用者選是 → 立即關機
    & shutdown /s /t 0
} else {
    # 使用者選否 → 取消倒數關機
    & shutdown /a
    [System.Windows.MessageBox]::Show(
        "已取消自動關機。",
        "TZG 電商",
        [System.Windows.MessageBoxButton]::OK,
        [System.Windows.MessageBoxImage]::Information
    ) | Out-Null
}
