@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ========================================
echo  ScanLoop Build Script
echo ========================================
echo.

:: --- Virtual environment ---
if not exist "venv\Scripts\python.exe" (
    echo [SETUP] Creating virtual environment...
    python -m venv venv
)
if errorlevel 1 (
    echo [FAIL] Could not create venv. Check Python installation.
    pause
    exit /b 1
)
if exist "venv\Scripts\python.exe" (
    echo [OK] Virtual environment ready.
)

:: --- Dependencies ---
echo [SETUP] Installing/updating dependencies...
call venv\Scripts\python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [WARN] pip install had issues. Attempting build anyway...
) else (
    echo [OK] Dependencies ready.
)

:: --- Build ---
echo [BUILD] Starting build...
echo [BUILD] Script: build\scripts\build_exe.py
echo.
call venv\Scripts\python build\scripts\build_exe.py
set BUILD_EXIT=%ERRORLEVEL%

echo.
if %BUILD_EXIT% neq 0 (
    echo [FAIL] Build failed with exit code %BUILD_EXIT%.
) else (
    echo [OK] Build completed successfully.
)
echo ========================================
pause
exit /b %BUILD_EXIT%
