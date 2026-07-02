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
set "SETUP_URL=https://raw.githubusercontent.com/BT-Rajan/knpc-dashboard/main/installer/setup_and_play.py"

if exist "%SETUP_PY%" del "%SETUP_PY%" >nul 2>nul

:: Try curl first - it ships with Windows 10 (1803+) and Windows 11, and
:: handles TLS negotiation more reliably than older PowerShell defaults.
where curl >nul 2>nul
if %errorlevel%==0 (
    curl -fsSL "%SETUP_URL%" -o "%SETUP_PY%" >nul 2>nul
)

:: Fall back to PowerShell, explicitly forcing TLS 1.2 - some older
:: Windows/PowerShell combinations default to TLS 1.0/1.1, which GitHub
:: rejects, causing Invoke-WebRequest to fail with no useful message.
if not exist "%SETUP_PY%" (
    %_ps% "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri '%SETUP_URL%' -OutFile '%SETUP_PY%' -UseBasicParsing } catch { Write-Host $_.Exception.Message -ForegroundColor Red; exit 1 }"
)

if not exist "%SETUP_PY%" (
    %_ps% "Write-Host ''"
    %_ps% "Write-Host 'Could not download the setup program.' -ForegroundColor Red"
    %_ps% "Write-Host 'This is usually one of the following:' -ForegroundColor Yellow"
    %_ps% "Write-Host '  - No internet connection right now' -ForegroundColor Yellow"
    %_ps% "Write-Host '  - A company firewall or proxy blocking github.com' -ForegroundColor Yellow"
    %_ps% "Write-Host '  - An outdated Windows/PowerShell TLS setting' -ForegroundColor Yellow"
    %_ps% "Write-Host ''"
    %_ps% "Write-Host 'You can also open this link directly in your browser and save the file yourself:' -ForegroundColor Yellow"
    %_ps% "Write-Host '  %SETUP_URL%' -ForegroundColor Cyan"
    echo.
    pause
    exit /b 1
)

%_ps% "Write-Host 'Ready. Launching setup...' -ForegroundColor Green"
echo.

"%PYCMD%" "%SETUP_PY%"

endlocal

