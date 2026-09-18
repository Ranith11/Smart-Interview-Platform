@echo off
echo ===================================================
echo       SmartInterview - One-Click Start Script
echo ===================================================
echo.

:: 1. Database Setup Reminder
echo [INFO] Please make sure you have created the .env file with GROQ_API_KEY.
echo [INFO] Please make sure MySQL is running and the database is imported.
echo.

:: 2. Setup and Start Backend
echo [1/2] Starting Backend Server...
cd backend
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [INFO] Installing backend requirements...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)
:: Start backend in a new command window
start "SmartInterview Backend" cmd /k "uvicorn app.main:app --reload"
cd ..

:: 3. Setup and Start Frontend
echo [2/2] Starting Frontend Server...
cd frontend
if not exist "node_modules" (
    echo [INFO] Installing frontend dependencies...
    call npm install
)
:: Start frontend in a new command window
start "SmartInterview Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ===================================================
echo Done! 
echo Backend is running at: http://localhost:8000
echo Frontend is running at: http://localhost:5173
echo ===================================================
