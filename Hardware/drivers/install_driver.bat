@echo off
REM ============================================================
REM  Thorlabs PM100D — Install WinUSB driver via Zadig
REM  Run as Administrator!
REM ============================================================
setlocal
title Thorlabs PM100D Driver Installer

echo.
echo  === Thorlabs PM100D Driver Installer ===
echo.
echo  This script installs a WinUSB driver for PM100D.
echo  WinUSB is built into Windows 7+, no Thorlabs software needed.
echo.
echo  Requirements:
echo    - PM100D connected via USB
echo    - Run as Administrator
echo.

REM Check admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Run this script as Administrator!
    echo Right-click on install_driver.bat - select "Run as administrator"
    pause
    exit /b 1
)

REM Check if Zadig exists
set ZADIG=%~dp0zadig.exe
if not exist "%ZADIG%" (
    echo Downloading Zadig (free USB driver installer)...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/pbatard/libwdi/releases/download/v1.5.1/zadig-2.9.exe' -OutFile '%ZADIG%'" 2>nul
    if not exist "%ZADIG%" (
        echo.
        echo ERROR: Could not download Zadig automatically.
        echo Please download manually from: https://zadig.akeo.ie/
        echo Save it to: %~dp0
        pause
        exit /b 1
    )
    echo Zadig downloaded successfully.
)

echo.
echo Launching Zadig...
echo.
echo  INSTRUCTIONS:
echo  1. In Zadig menu: Options -^> List All Devices
echo  2. Select "PM100D" from the dropdown
echo  3. Select "WinUSB" driver (green arrow)
echo  4. Click "Replace Driver" or "Install Driver"
echo  5. Wait for "Driver Installation: SUCCESS"
echo  6. Close Zadig
echo.

start "" "%ZADIG%"
echo Zadig is running. Follow the instructions above.
echo After installing the driver, press any key to test.
pause >nul

echo.
echo Testing connection...
python "%~dp0test_connection.py"
if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: PM100D driver installed and working!
) else (
    echo.
    echo Connection test failed. Make sure:
    echo   1. PM100D is connected
    echo   2. Driver was installed successfully in Zadig
    echo   3. No other software is using the PM100D
)
pause
