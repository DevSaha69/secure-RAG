@echo off
echo Starting Secure-RAG Backend API...
start "Secure-RAG Backend" cmd /k ".\venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting Secure-RAG Frontend UI...
cd frontend
start "Secure-RAG Frontend" cmd /k "npm.cmd run dev"

echo Waiting for servers to initialize...
timeout /t 5 >nul

echo Opening website in browser...
start http://localhost:5173/

echo Website started successfully! You can close this window.
