@echo off
chcp 65001 >nul
cd /d "%~dp0"

set PYTHONIOENCODING=utf-8

python edit_targets.py

if errorlevel 1 (
    echo.
    echo [!] 執行時發生錯誤，按任意鍵關閉
    pause >nul
)
