@echo off
chcp 65001 >nul
echo ========================================
echo 🧹 LIMPAR CACHE E REINICIAR
echo ========================================
echo.

echo 1. Fechando processos Python antigos...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul
timeout /t 2 /nobreak >nul

echo 2. Limpando arquivos .pyc (cache)...
del /S /Q src\__pycache__\*.* 2>nul
del /S /Q __pycache__\*.* 2>nul
rmdir /S /Q src\__pycache__ 2>nul
rmdir /S /Q __pycache__ 2>nul

echo 3. Recompilando código...
".venv\Scripts\python.exe" -m compileall src -f -q

echo 4. Verificando configuração...
".venv\Scripts\python.exe" -c "import json; c=json.load(open(r'%USERPROFILE%\.tradutor_master\config.json')); print(f'\nModelo atual: {c.get(\"claude_model\", \"NAO DEFINIDO\")}')"

echo.
echo ✅ Limpeza completa!
echo.
echo Agora pode executar o Tradutor Master normalmente.
echo.
pause
