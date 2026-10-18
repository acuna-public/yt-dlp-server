@echo off

cd /d "%~dp0"

cd ..

.venv\Scripts\python.exe src\run.py

echo.
pause