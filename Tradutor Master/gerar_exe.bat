@echo off
chcp 65001 >nul
echo ========================================
echo   Gerador de Executável - Arquivo Único
echo   Usando PyInstaller do VENV
echo ========================================
echo.

REM Verificar se venv existe
if not exist ".venv\Scripts\activate.bat" (
    echo ❌ Erro: Ambiente virtual não encontrado
    echo    Execute: python -m venv .venv
    pause
    exit /b 1
)

REM Ativar ambiente virtual
echo [1/5] Ativando ambiente virtual...
call .venv\Scripts\activate.bat
echo ✓ Ambiente virtual ativado
echo.

REM Instalar PyInstaller no venv
echo [2/5] Instalando PyInstaller no venv...
.venv\Scripts\python.exe -m pip install pyinstaller --quiet
if errorlevel 1 (
    echo ❌ Erro ao instalar PyInstaller
    pause
    exit /b 1
)
echo ✓ PyInstaller instalado
echo.

REM Limpar builds anteriores
echo [3/5] Limpando builds anteriores...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"
echo ✓ Limpeza concluída
echo.

REM Gerar executável usando PyInstaller do venv
echo [4/5] Gerando executável (arquivo único)...
echo    Usando Python do venv: %CD%\.venv\Scripts\python.exe
echo    Isso pode levar 5-10 minutos...
echo.

.venv\Scripts\pyinstaller.exe --noconfirm ^
    --onefile ^
    --windowed ^
    --name "TradutorMaster" ^
    --add-data "src;src" ^
    --hidden-import=anthropic ^
    --hidden-import=anthropic.types ^
    --hidden-import=anthropic.resources ^
    --hidden-import=mysql.connector ^
    --hidden-import=mysql.connector.pooling ^
    --hidden-import=requests ^
    --hidden-import=docx ^
    --hidden-import=openpyxl ^
    --hidden-import=pptx ^
    --hidden-import=pdf2docx ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.ttk ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=lxml ^
    --hidden-import=lxml.etree ^
    --paths=.venv\Lib\site-packages ^
    src/main.py

if errorlevel 1 (
    echo.
    echo ❌ Erro ao gerar executável
    pause
    exit /b 1
)

echo.
echo ✓ Executável gerado!
echo.

REM Verificar resultado
echo [5/5] Verificando resultado...
if exist "dist\TradutorMaster.exe" (
    echo.
    echo ========================================
    echo   ✅ SUCESSO!
    echo ========================================
    echo.
    echo 📦 Executável criado em:
    echo    %CD%\dist\TradutorMaster.exe
    echo.
    echo 📊 Tamanho do arquivo:
    for %%A in ("dist\TradutorMaster.exe") do echo    %%~zA bytes
    echo.
    echo 💡 Distribua apenas o arquivo .exe
    echo.
) else (
    echo ❌ Executável não foi criado
)

echo.
pause
