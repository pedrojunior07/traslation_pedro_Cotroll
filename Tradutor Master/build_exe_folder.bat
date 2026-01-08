@echo off
echo ========================================
echo   CONSTRUINDO EXECUTAVEL DO TRADUTOR
echo   (Versao em pasta - mais rapido)
echo ========================================
echo.

REM Ativar ambiente virtual
call .venv\Scripts\activate.bat

REM Instalar PyInstaller se necessário
echo Verificando PyInstaller...
pip install pyinstaller

REM Limpar builds anteriores
echo.
echo Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "Tradutor Master.spec" del "Tradutor Master.spec"

REM Criar executável em pasta
echo.
echo Criando executavel...
pyinstaller --onedir ^
    --windowed ^
    --name "Tradutor Master" ^
    --paths=src ^
    --collect-all anthropic ^
    --collect-all pdf2docx ^
    --collect-all fitz ^
    --collect-all docx ^
    --collect-all mysql ^
    --collect-submodules docx ^
    --hidden-import=anthropic ^
    --hidden-import=requests ^
    --hidden-import=mysql.connector ^
    --hidden-import=pdf2docx ^
    --hidden-import=docx ^
    --hidden-import=docx.shared ^
    --hidden-import=docx.oxml ^
    --hidden-import=fitz ^
    --hidden-import=PyMuPDF ^
    --hidden-import=tkinter ^
    --hidden-import=PIL ^
    --hidden-import=tkinter.ttk ^
    --hidden-import=tkinter.filedialog ^
    --hidden-import=tkinter.messagebox ^
    --hidden-import=_tkinter ^
    --copy-metadata python-docx ^
    --noupx ^
    --noconsole ^
    src\main.py

echo.
echo ========================================
echo   BUILD CONCLUIDO!
echo ========================================
echo.
echo Executavel criado em: dist\Tradutor Master\Tradutor Master.exe
echo.
pause
