@echo off
setlocal
color 0D
title Candy

echo.
echo   /*  ++----------------------------------------------------------++  */
echo   /*                      [ by Candy ]                                */
echo   /*  ++----------------------------------------------------------++  */
echo.
echo   Checking for Python...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python not found!
    echo   Download from: https://www.python.org/downloads/
    echo   Make sure to check "Add Python to PATH" when installing!
    echo.
    pause
    exit
)

echo   Installing required packages...
python -m pip install requests --quiet --disable-pip-version-check

echo   Launching Candy...
echo.
timeout /t 1 /nobreak >nul

python "%~dp0candy_checker.py"

if errorlevel 1 (
    echo.
    echo   Error! Make sure candy_checker.py is in the same folder as Candy.bat
    echo.
    pause
)
