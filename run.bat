@echo off
cd /d "%~dp0"

echo === Agora Social Simulation ===
echo.

REM Check if venv exists, create if not
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Start the server
echo.
echo Starting Agora server...
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
