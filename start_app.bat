@echo off
cls

echo ==========================================
echo Project Management Platform Start Script
echo ==========================================
echo Select Startup Mode:
echo 1. Development Mode (Debug Mode)
echo 2. Production Mode (Production Mode)
echo ==========================================

set /p choice=Enter option (1/2): 

if "%choice%"=="1" (
    echo Starting Development Mode...
    echo Setting environment variable FLASK_ENV=development
    set FLASK_ENV=development
    
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
    
    echo Starting Flask application...
    python app.py
) else if "%choice%"=="2" (
    echo Starting Production Mode...
    echo Setting environment variable FLASK_ENV=production
    set FLASK_ENV=production
    
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
    
    echo Starting Flask application...
    python app.py
) else (
    echo Invalid choice. Please run the script again and enter 1 or 2.
    pause
    exit /b 1
)