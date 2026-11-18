@echo off
setlocal
cd /d "%~dp0"
echo Installation des dependances...
py -m pip install --upgrade pip
py -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto error
echo Construction de GESCO...
py -m PyInstaller --noconfirm --clean --windowed --name GESCO --collect-all PySide6 main.py
if errorlevel 1 goto error
echo.
echo Compilation terminee. Application disponible dans dist\GESCO\
pause
exit /b 0
:error
echo Une erreur est survenue pendant la compilation.
pause
exit /b 1
