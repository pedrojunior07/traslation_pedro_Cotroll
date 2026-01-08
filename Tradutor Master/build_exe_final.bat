@echo off
echo ========================================
echo   TRADUTOR MASTER - BUILD FINAL
echo   Resolve todos os erros de import
echo ========================================
echo.

REM Ativar ambiente virtual
call .venv\Scripts\activate.bat

REM Atualizar PyInstaller
echo Atualizando PyInstaller...
pip install --upgrade pyinstaller

REM Limpar TUDO
echo.
echo Limpando builds e cache...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
if exist "Tradutor Master.spec" del "Tradutor Master.spec"
rmdir /s /q %LOCALAPPDATA%\pyinstaller 2>nul

REM Criar executável COM TODAS AS CORREÇÕES
echo.
echo Criando executavel (pode demorar 2-3 minutos)...
echo.

pyinstaller ^
    --onedir ^
    --name "Tradutor Master" ^
    --noconfirm ^
    --clean ^
    --additional-hooks-dir=. ^
    --collect-all docx ^
    --collect-all pdf2docx ^
    --collect-all fitz ^
    --collect-all anthropic ^
    --collect-all mysql ^
    --collect-submodules docx ^
    --collect-submodules pdf2docx ^
    --collect-binaries fitz ^
    --hidden-import=docx ^
    --hidden-import=docx.shared ^
    --hidden-import=docx.oxml ^
    --hidden-import=docx.oxml.ns ^
    --hidden-import=docx.oxml.text ^
    --hidden-import=docx.oxml.xmlchemy ^
    --hidden-import=docx.text ^
    --hidden-import=docx.text.paragraph ^
    --hidden-import=docx.enum ^
    --hidden-import=docx.enum.text ^
    --hidden-import=pdf2docx ^
    --hidden-import=fitz ^
    --hidden-import=PyMuPDF ^
    --hidden-import=anthropic ^
    --hidden-import=requests ^
    --hidden-import=mysql.connector ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.ttk ^
    --hidden-import=tkinter.filedialog ^
    --hidden-import=tkinter.messagebox ^
    --hidden-import=_tkinter ^
    --copy-metadata python-docx ^
    --copy-metadata pdf2docx ^
    --copy-metadata anthropic ^
    --noupx ^
    --noconsole ^
    src\main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo   ERRO NO BUILD!
    echo ========================================
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   BUILD CONCLUIDO COM SUCESSO!
echo ========================================
echo.
echo Executavel criado em: dist\Tradutor Master\
echo.
echo Testando executavel...
cd "dist\Tradutor Master"
"Tradutor Master.exe"

pause
