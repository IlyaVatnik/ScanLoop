@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

:: --- Retry guard (prevents winget infinite loop) ---
if "%_RETRY%"=="" set _RETRY=0

:: --- Python check ---
python --version >nul 2>&1
if errorlevel 1 goto :no_python

:: --- Version check (need 3.10+) ---
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
    goto :old_python
)

:: --- pip check ---
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing pip...
    python -m ensurepip --upgrade
)

goto :build_start

:no_python
echo.
echo ========================================
echo  Python not found!
echo ========================================
echo.

:python_menu
echo  Choose an option:
echo    0) Cancel build
echo    1) Install Python (via winget)
echo    2) Show download link
echo    3) Skip check (if Python is already available)
echo.
choice /C 0123 /N /M "Your choice (0/1/2/3): "
if errorlevel 4 goto :python_cont
if errorlevel 3 goto :python_showlink
if errorlevel 2 goto :python_install
if errorlevel 1 exit /b 0

:python_install
winget --version >nul 2>&1
if errorlevel 1 (
    echo [WARN] winget not available (needs Windows 10 1809+).
    echo        Please install Python manually.
    goto :python_showlink
)
if %_RETRY% geq 2 (
    echo [FAIL] Winget failed twice. Install Python manually.
    goto :python_showlink
)
echo.
echo [SETUP] Installing Python via winget...
winget install Python.Python.3 --silent --accept-package-agreements
if errorlevel 1 (
    echo [FAIL] Winget install failed.
    set /a _RETRY+=1
    goto :python_menu
)
echo [OK] Python installed. Restarting build to pick up PATH...
set _RETRY=1
call "%~f0"
exit /b 0

:python_showlink
echo.
echo  Download Python 3.x from:
echo  https://www.python.org/downloads/
echo.
echo  IMPORTANT: during installation, check
echo  "Add Python to PATH" at the bottom.
echo.
pause
goto :python_menu

:python_cont
echo.
echo  [WARN] Skipping Python check. Build may fail.
goto :build_start

:old_python
echo.
echo ========================================
echo  Python %PY_VER% is too old!
echo  Need Python 3.10 or later.
echo ========================================
echo.
goto :python_menu

:build_start
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
    echo [FAIL] Could not create virtual environment.
    echo        Try running: python -m venv venv
    pause
    exit /b 1
)
echo [OK] Virtual environment ready.

:: --- Dependencies ---
echo [SETUP] Installing/updating dependencies...
call venv\Scripts\python -m pip install -r build\scripts\requirements.txt
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
