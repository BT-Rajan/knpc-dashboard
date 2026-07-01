@echo off
setlocal EnableDelayedExpansion
title KNPC Installer & Launcher

:: ============================================================
:: CONFIGURATION
:: ============================================================

set APP_NAME=KNPC Market Intelligence
set APP_FILE=app.py

set REQUIRED_FILES=app.py database.py analytics.py exporter.py config.py main.py animation.html

set "_ps=powershell -NoProfile -ExecutionPolicy Bypass -Command"

:: ============================================================
:: COLOR FUNCTIONS
:: ============================================================

goto :main

:log
%_ps% "Write-Host '%~1' -ForegroundColor Cyan"
goto :eof

:success
%_ps% "Write-Host '%~1' -ForegroundColor Green"
goto :eof

:error
%_ps% "Write-Host '%~1' -ForegroundColor Red"
goto :eof

:warn
%_ps% "Write-Host '%~1' -ForegroundColor Yellow"
goto :eof

:progress
%_ps% "Write-Host ('Progress: [' + ('=' * (%1/5)) + '] %1%%') -ForegroundColor DarkCyan"
goto :eof


:: ============================================================
:: MAIN
:: ============================================================

:main

cls
echo.
echo ==========================================================
echo            %APP_NAME% INSTALLER
echo ==========================================================
echo.

:: ------------------------------------------------------------
:: STEP 1 CHECK PYTHON
:: ------------------------------------------------------------

call :progress 10
call :log "[STEP 1/9] Checking Python installation..."

python --version >nul 2>&1

if errorlevel 1 (
    call :error "ERROR: Python not installed or missing from PATH."
    call :warn "Download Python from https://www.python.org/downloads/"
    pause
    exit /b 1
)

call :success "SUCCESS: Python detected."
timeout /t 1 >nul


:: ------------------------------------------------------------
:: STEP 2 SECURITY POLICY
:: ------------------------------------------------------------

call :progress 20
call :log "[STEP 2/9] Applying temporary PowerShell execution policy..."

powershell -Command "Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force" >nul 2>&1

call :success "SUCCESS: Security policy updated."
timeout /t 1 >nul


:: ------------------------------------------------------------
:: STEP 3 FILE VALIDATION
:: ------------------------------------------------------------

call :progress 30
call :log "[STEP 3/9] Validating application files..."

for %%f in (%REQUIRED_FILES%) do (
    if not exist %%f (
        call :error "ERROR: Missing required file -> %%f"
        pause
        exit /b 1
    )
)

call :success "SUCCESS: All required files found."
timeout /t 1 >nul


:: ------------------------------------------------------------
:: STEP 4 REQUIREMENTS FILE
:: ------------------------------------------------------------

call :progress 40
call :log "[STEP 4/9] Checking requirements.txt..."

if not exist requirements.txt (
    call :warn "requirements.txt missing. Creating default file..."

    (
        echo streamlit
        echo pandas
        echo openpyxl
    ) > requirements.txt
)

call :success "SUCCESS: requirements.txt ready."
timeout /t 1 >nul


:: ------------------------------------------------------------
:: STEP 5 CREATE VENV
:: ------------------------------------------------------------

call :progress 50
call :log "[STEP 5/9] Creating Python virtual environment..."

if not exist venv (
    python -m venv venv

    if errorlevel 1 (
        call :error "ERROR: Could not create virtual environment."
        pause
        exit /b 1
    )
)

call :success "SUCCESS: Virtual environment ready."
timeout /t 1 >nul


:: ------------------------------------------------------------
:: STEP 6 ACTIVATE ENVIRONMENT
:: ------------------------------------------------------------

call :progress 60
call :log "[STEP 6/9] Activating virtual environment..."

call venv\Scripts\activate.bat

if errorlevel 1 (
    call :error "ERROR: Failed to activate environment."
    pause
    exit /b 1
)

call :success "SUCCESS: Environment activated."
timeout /t 1 >nul


:: ------------------------------------------------------------
:: STEP 7 INSTALL / REPAIR PACKAGES
:: ------------------------------------------------------------

call :progress 70
call :log "[STEP 7/9] Installing dependencies..."

python -m pip install --upgrade pip >nul 2>&1

pip install -r requirements.txt

if errorlevel 1 (
    call :warn "Dependency install failed. Attempting repair..."

    pip install streamlit pandas openpyxl --upgrade

    if errorlevel 1 (
        call :error "ERROR: Package installation failed."
        pause
        exit /b 1
    )
)

call :success "SUCCESS: Dependencies installed."
timeout /t 1 >nul


:: ------------------------------------------------------------
:: STEP 8 DESKTOP SHORTCUT
:: ------------------------------------------------------------

call :progress 85
call :log "[STEP 8/9] Creating desktop shortcut..."

set SCRIPT=%temp%\shortcut.vbs

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%SCRIPT%"
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\KNPC Launcher.lnk" >> "%SCRIPT%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%SCRIPT%"
echo oLink.TargetPath = "%cd%\installer.bat" >> "%SCRIPT%"
echo oLink.WorkingDirectory = "%cd%" >> "%SCRIPT%"
echo oLink.Save >> "%SCRIPT%"

cscript /nologo "%SCRIPT%" >nul 2>&1
del "%SCRIPT%"

call :success "SUCCESS: Desktop shortcut created."
timeout /t 1 >nul


:: ------------------------------------------------------------
:: STEP 9 START APP
:: ------------------------------------------------------------

call :progress 100
call :log "[STEP 9/9] Starting Streamlit server..."

:: start server without auto browser open
start /B python -m streamlit run app.py --server.headless true

timeout /t 20 >nul

call :success "SUCCESS: Opening application in browser..."

:: open browser only ONCE
start http://localhost:8501

echo.
call :success "INSTALLATION COMPLETE"
echo.

exit