@echo off
echo Iniciando Tradutor Master (Nova UI)...
echo.
cd /d "%~dp0\src"
..\.venv\Scripts\python.exe main.py
pause
