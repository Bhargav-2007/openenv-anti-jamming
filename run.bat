@echo off
REM Quick startup script for Anti-Jamming OpenEnv on Windows

setlocal enabledelayedexpansion

echo.
echo 🛰️  Anti-Jamming OpenEnv - Quick Setup
echo ======================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python found: %PYTHON_VERSION%

REM Create venv if needed
if not exist "venv" (
    echo.
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
)

REM Activate venv
echo.
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
if not exist ".deps_installed" (
    echo.
    echo 📥 Installing dependencies...
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    type nul > .deps_installed
    echo ✅ Dependencies installed
)

REM Run server
echo.
echo 🚀 Starting Anti-Jamming OpenEnv Server...
echo.
echo 🌐 Frontend: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo WebSocket: ws://localhost:8000/ws
echo.
echo Press Ctrl+C to stop
echo.

python api_server.py

pause
