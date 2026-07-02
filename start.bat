@echo off
setlocal EnableDelayedExpansion
title KNPC Business Data Intelligence Platform - Setup

:: ============================================================
:: KNPC Business Data Intelligence Platform - Setup Launcher
:: Checks Python, then runs the console installer already sitting
:: in this repo's installer\ folder. Nothing is downloaded over
:: the network - if you have this file, you already have the rest
:: of the project it belongs to.
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
%_ps% "Write-Host 'Checking whether Python is installed...' -ForegroundColor White"

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
:: STEP 1: RUN THE LOCAL CONSOLE INSTALLER
:: ------------------------------------------------------------
set "SETUP_PY=%~dp0installer\setup_and_play.py"

if not exist "%SETUP_PY%" (
    %_ps% "Write-Host 'Could not find installer\setup_and_play.py next to this file.' -ForegroundColor Red"
    %_ps% "Write-Host 'Make sure start.bat stayed inside the project folder it came with.' -ForegroundColor Yellow"
    echo.
    pause
    exit /b 1
)

"%PYCMD%" "%SETUP_PY%"

endlocal
