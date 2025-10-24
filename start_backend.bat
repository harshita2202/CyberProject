@echo off
echo 🛡️ Phishing Detector Extension - Backend Startup
echo ================================================

cd /d "%~dp0"

echo 🔍 Checking if Python is installed...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found

echo 🔍 Checking if backend directory exists...
if not exist "backend" (
    echo ❌ Backend directory not found
    echo Please make sure you're in the correct project directory
    pause
    exit /b 1
)

echo ✅ Backend directory found

echo 🔍 Checking if backend is already running...
curl -s http://localhost:5000/health >nul 2>&1
if not errorlevel 1 (
    echo ✅ Backend is already running at http://localhost:5000
    echo 🎉 You can now use the Phishing Detector Extension!
    pause
    exit /b 0
)

echo 🔄 Starting backend server...
cd backend

echo 📦 Installing requirements...
pip install -r requirements.txt

echo 🚀 Starting Flask server...
echo.
echo ✅ Backend is starting...
echo 🌐 Server will be available at: http://localhost:5000
echo 📊 Health check: http://localhost:5000/health
echo.
echo 💡 You can now use the Phishing Detector Extension!
echo 🔄 To stop the server, press Ctrl+C
echo.

python app.py

echo.
echo ⏹️ Backend server stopped
pause
