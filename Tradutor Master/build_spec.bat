@echo off
echo ========================================
echo   BUILD COM SPEC FILE (RECOMENDADO)
echo ========================================
echo.

REM Ativar ambiente virtual
call .venv\Scripts\activate.bat

REM Limpar builds anteriores
echo Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build usando spec file
echo.
echo Compilando executavel usando tradutor.spec...
pyinstaller --clean --noconfirm tradutor.spec

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERRO NO BUILD!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   BUILD CONCLUIDO!
echo ========================================
echo.
echo Executavel: dist\Tradutor Master\Tradutor Master.exe
echo.
pause
