@echo off
echo ========================================
echo   BUILD MANUAL - COPIA MODULOS
echo   Solucao definitiva para erro docx
echo ========================================
echo.

REM Ativar ambiente virtual
call .venv\Scripts\activate.bat

REM Limpar
echo Limpando...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build básico primeiro
echo.
echo Passo 1: Build basico do PyInstaller...
pyinstaller --onedir --name "Tradutor Master" --noconsole --clean --noconfirm src\main.py

if %ERRORLEVEL% NEQ 0 (
    echo ERRO no build!
    pause
    exit /b 1
)

REM Copiar módulos manualmente
echo.
echo Passo 2: Copiando modulos python-docx, pdf2docx, fitz, typing_extensions...

REM Criar pasta _internal se não existir
if not exist "dist\Tradutor Master\_internal" mkdir "dist\Tradutor Master\_internal"

REM Copiar python-docx
echo   - Copiando docx...
xcopy /E /I /Y /Q ".venv\Lib\site-packages\docx" "dist\Tradutor Master\_internal\docx" >nul

REM Copiar lxml (dependência do docx)
echo   - Copiando lxml...
xcopy /E /I /Y /Q ".venv\Lib\site-packages\lxml" "dist\Tradutor Master\_internal\lxml" >nul

REM Copiar typing_extensions (dependência do docx) - CRÍTICO!
echo   - Copiando typing_extensions...
copy /Y ".venv\Lib\site-packages\typing_extensions.py" "dist\Tradutor Master\_internal\" >nul

REM Copiar pdf2docx
echo   - Copiando pdf2docx...
xcopy /E /I /Y /Q ".venv\Lib\site-packages\pdf2docx" "dist\Tradutor Master\_internal\pdf2docx" >nul

REM Copiar fitz/PyMuPDF
echo   - Copiando fitz...
if exist ".venv\Lib\site-packages\fitz" (
    xcopy /E /I /Y /Q ".venv\Lib\site-packages\fitz" "dist\Tradutor Master\_internal\fitz" >nul
)

REM Copiar anthropic
echo   - Copiando anthropic...
if exist ".venv\Lib\site-packages\anthropic" (
    xcopy /E /I /Y /Q ".venv\Lib\site-packages\anthropic" "dist\Tradutor Master\_internal\anthropic" >nul
)

REM Copiar mysql
echo   - Copiando mysql...
if exist ".venv\Lib\site-packages\mysql" (
    xcopy /E /I /Y /Q ".venv\Lib\site-packages\mysql" "dist\Tradutor Master\_internal\mysql" >nul
)

REM Copiar PIL/Pillow
echo   - Copiando PIL...
if exist ".venv\Lib\site-packages\PIL" (
    xcopy /E /I /Y /Q ".venv\Lib\site-packages\PIL" "dist\Tradutor Master\_internal\PIL" >nul
)

REM Copiar requests
echo   - Copiando requests...
if exist ".venv\Lib\site-packages\requests" (
    xcopy /E /I /Y /Q ".venv\Lib\site-packages\requests" "dist\Tradutor Master\_internal\requests" >nul
)

echo.
echo ========================================
echo   BUILD CONCLUIDO!
echo ========================================
echo.
echo Executavel: dist\Tradutor Master\Tradutor Master.exe
echo.
echo Testando...
cd "dist\Tradutor Master"
"Tradutor Master.exe"

pause
