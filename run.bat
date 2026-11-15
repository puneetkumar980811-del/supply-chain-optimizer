@echo off
title OptiChain - Supply Chain Optimizer
color 0B

echo ========================================================
echo    OptiChain: Supply Chain Optimizer
echo    College Mini-Project in Operations Research
echo ========================================================
echo.

echo [1/3] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from python.org
    pause
    exit /b 1
)
python --version

echo.
echo [2/3] Checking dependencies...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [WARNING] Some dependencies failed to install. Attempting to start anyway...
)

echo.
echo [3/3] Launching OptiChain Streamlit Dashboard...
echo Dashboard will automatically open in your default browser.
echo Press Ctrl+C in this terminal window to stop the server.
echo.

python -m streamlit run app.py

pause
