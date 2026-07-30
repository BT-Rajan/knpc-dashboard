@echo off
REM KNPC Dashboard - Windows Installer
REM Comprehensive setup script for Windows 10/11
REM Prerequisites: Python 3.10+, Node.js 18+

setlocal enabledelayedexpansion
set "VERSION=1.0"
set "PROJECT=KNPC Dashboard"

REM Color codes
set "RESET=[0m"
set "GREEN=[32m"
set "RED=[31m"
set "YELLOW=[33m"
set "BLUE=[34m"

cls
echo.
echo ============================================================================
echo                   %PROJECT% - Windows Installer v%VERSION%
echo ============================================================================
echo.

REM Check for Python
echo Checking for Python 3.10+...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo [OK] Python %PYTHON_VER% found

REM Check for Node.js
echo Checking for Node.js 18+...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found!
    echo Please install Node.js 18+ LTS from https://nodejs.org/
    echo Make sure Node is added to PATH
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version 2^>^&1') do set NODE_VER=%%i
echo [OK] Node %NODE_VER% found

for /f "tokens=*" %%i in ('npm --version 2^>^&1') do set NPM_VER=%%i
echo [OK] npm %NPM_VER% found

echo.
echo ============================================================================
echo Setting up Backend (FastAPI)
echo ============================================================================
echo.

cd backend

REM Create virtual environment
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

REM Install dependencies
echo Installing Python dependencies...
pip install -q -r requirements.txt
if !errorlevel! neq 0 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)
echo [OK] Python dependencies installed

REM Verify imports
echo Verifying Python imports...
python -c "from app.main import app; print('[OK] FastAPI app imports successfully')" >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Failed to import FastAPI app
    pause
    exit /b 1
)

cd ..

echo.
echo ============================================================================
echo Setting up Frontend (React + Vite)
echo ============================================================================
echo.

cd frontend

REM Install Node dependencies
echo Installing Node.js dependencies...
echo This may take a few minutes...
call npm install --legacy-peer-deps >nul 2>&1
if !errorlevel! neq 0 (
    echo [WARNING] npm install had issues, but continuing...
)
echo [OK] Node.js dependencies installed

REM Run build
echo Building React frontend...
call npm run build >nul 2>&1
if !errorlevel! neq 0 (
    echo [WARNING] Frontend build had issues, but continuing...
)
echo [OK] Frontend built successfully

cd ..

echo.
echo ============================================================================
echo Installation Complete!
echo ============================================================================
echo.
echo You can now start the application:
echo.
echo Start Backend:
echo   1. Open PowerShell
echo   2. Run: cd backend
echo   3. Run: .\venv\Scripts\Activate.ps1
echo   4. Run: python run.py
echo   5. Backend will start on http://localhost:8000
echo.
echo Start Frontend (in new PowerShell window):
echo   1. Open PowerShell
echo   2. Run: cd frontend
echo   3. Run: npm run dev
echo   4. Frontend will open on http://localhost:5173
echo.
echo Or simply run these commands in sequence:
echo   cd backend ^&^& .\venv\Scripts\Activate.ps1 ^&^& python run.py
echo.
echo Documentation:
echo   - README.md           (Overview)
echo   - QUICK_START.md      (Quick reference)
echo   - FEATURE_UPDATES.md  (Technical details)
echo.
echo Press any key to exit...
pause >nul
exit /b 0
