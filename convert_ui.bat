@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Converting MainWindow.ui to MainWindowUI.py ===
python Windows_GUI/UIs/convert_ui.py
pause
