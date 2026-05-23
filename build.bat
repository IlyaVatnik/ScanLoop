@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Запуск сборки ScanLoop ===
python build_exe.py
pause
