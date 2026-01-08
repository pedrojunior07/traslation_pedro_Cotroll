@echo off
echo ========================================
echo   CONSTRUINDO EXECUTAVEL DO TRADUTOR
echo   (Modo Seguro - Resolve erro Ordinal)
echo ========================================
echo.

REM Ativar ambiente virtual
call .venv\Scripts\activate.bat

REM Atualizar PyInstaller para ultima versao
echo Atualizando PyInstaller...
pip install --upgrade pyinstaller

REM Limpar builds anteriores e cache
echo.
echo Limpando builds anteriores e cache...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
if exist "Tradutor Master.spec" del "Tradutor Master.spec"

REM Limpar cache do PyInstaller
rmdir /s /q %LOCALAPPDATA%\pyinstaller 2>nul

REM Criar executável em PASTA (mais estável)
echo.
echo Criando executavel em pasta (mais estavel)...
pyinstaller ^
    --onedir ^
    --name "Tradutor Master" ^
    --paths=src ^
    --collect-all anthropic ^
    --collect-all pdf2docx ^
    --collect-all fitz ^
    --collect-all docx ^
    --collect-all mysql ^
    --collect-submodules anthropic ^
    --collect-submodules pdf2docx ^
    --collect-submodules docx ^
    --collect-submodules mysql ^
    --hidden-import=anthropic ^
    --hidden-import=requests ^
    --hidden-import=mysql.connector ^
    --hidden-import=pdf2docx ^
    --hidden-import=docx ^
    --hidden-import=docx.shared ^
    --hidden-import=docx.oxml ^
    --hidden-import=docx.text ^
    --hidden-import=fitz ^
    --hidden-import=PyMuPDF ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.ttk ^
    --hidden-import=tkinter.filedialog ^
    --hidden-import=tkinter.messagebox ^
    --hidden-import=_tkinter ^
    --hidden-import=json ^
    --hidden-import=threading ^
    --copy-metadata anthropic ^
    --copy-metadata pdf2docx ^
    --copy-metadata python-docx ^
    --noupx ^
    --clean ^
    --noconfirm ^
    src\main.py

echo.
echo ========================================
echo   BUILD CONCLUIDO!
echo ========================================
echo.
echo Executavel criado em: dist\Tradutor Master\Tradutor Master.exe
echo.
echo IMPORTANTE: Copie a pasta INTEIRA "dist\Tradutor Master" para usar
echo.
pause
