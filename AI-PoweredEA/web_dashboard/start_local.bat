@echo off
echo 🚀 Starting Gold Trading Dashboard...
echo.

echo 📦 Installing Backend Dependencies...
cd backend
pip install fastapi uvicorn websockets MetaTrader5 pandas numpy sqlite3 asyncio logging datetime pathlib typing dataclasses json
echo.

echo 🔥 Starting Backend Server...
start "Gold Dashboard Backend" cmd /k "python main.py"
timeout /t 3

echo.
echo 📱 Installing Frontend Dependencies...
cd ..\frontend
call npm install
echo.

echo 🌐 Starting Frontend Server...
start "Gold Dashboard Frontend" cmd /k "npm start"

echo.
echo ✅ Gold Trading Dashboard is starting...
echo 📊 Backend API: http://localhost:8000
echo 🖥️  Frontend UI: http://localhost:3000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Press any key to exit...
pause
