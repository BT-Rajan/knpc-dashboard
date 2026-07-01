@echo off
setlocal EnableDelayedExpansion
title KNPC Business Data Intelligence Platform - Setup

:: ============================================================
:: KNPC Business Data Intelligence Platform - Setup Launcher
:: Checks Python, then hands off to a console installer that
:: downloads the app, sets it up, and runs a trivia quiz (or a
:: quiet progress view) while it works.
:: ============================================================

set "_ps=powershell -NoProfile -ExecutionPolicy Bypass -Command"

:: ------------------------------------------------------------
:: BANNER
:: ------------------------------------------------------------
cls
%_ps% "Write-Host ''"
%_ps% "Write-Host '=============================================================' -ForegroundColor Cyan"
%_ps% "Write-Host '   KNPC Business Data Intelligence Platform - Setup' -ForegroundColor Cyan"
%_ps% "Write-Host '=============================================================' -ForegroundColor Cyan"
%_ps% "Write-Host ''"

:: ------------------------------------------------------------
:: STEP 0: CHECK PYTHON
:: ------------------------------------------------------------
%_ps% "Write-Host '[1/2] Checking whether Python is installed...' -ForegroundColor White"

set "PYCMD="
python --version >nul 2>nul
if %errorlevel%==0 (
    set "PYCMD=python"
) else (
    py --version >nul 2>nul
    if %errorlevel%==0 (
        set "PYCMD=py"
    )
)

if "%PYCMD%"=="" (
    %_ps% "Write-Host 'Python was not found on this computer, or it is not on your PATH.' -ForegroundColor Red"
    %_ps% "Write-Host ''"
    %_ps% "Write-Host 'Opening the Python download page for you now...' -ForegroundColor Yellow"
    start "" https://www.python.org/downloads/
    %_ps% "Write-Host ''"
    %_ps% "Write-Host 'During setup, be sure to check the box that says Add Python to PATH - it is easy to miss.' -ForegroundColor Yellow"
    %_ps% "Write-Host ''"
    %_ps% "Write-Host 'Once installed, just run this file again.' -ForegroundColor Yellow"
    echo.
    pause
    exit /b 1
)

%_ps% "Write-Host 'Python found. Good to go.' -ForegroundColor Green"
echo.

:: ------------------------------------------------------------
:: STEP 1: FETCH AND LAUNCH THE CONSOLE INSTALLER
:: ------------------------------------------------------------
%_ps% "Write-Host '[2/2] Fetching the setup program...' -ForegroundColor White"

set "TEMPDIR=%TEMP%\knpc_installer_bootstrap"
if not exist "%TEMPDIR%" mkdir "%TEMPDIR%" >nul 2>nul
set "SETUP_PY=%TEMPDIR%\setup_and_play.py"

%_ps% "try { Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/BT-Rajan/knpc-dashboard/main/installer/setup_and_play.py' -OutFile '%SETUP_PY%' -UseBasicParsing } catch { exit 1 }"

if not exist "%SETUP_PY%" (
    %_ps% "Write-Host 'Could not download the setup program. Check your internet connection and try again.' -ForegroundColor Red"
    echo.
    pause
    exit /b 1
)

%_ps% "Write-Host 'Ready. Launching setup...' -ForegroundColor Green"
echo.

"%PYCMD%" "%SETUP_PY%"

endlocal
