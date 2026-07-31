@echo off
REM Instala as dependencias (se necessario) e abre a tela do DIFAL Bot Sebem.

cd /d "%~dp0"

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERRO ao instalar as dependencias. Verifique se o Python esta instalado.
    pause
    exit /b 1
)

python -m streamlit run app.py

pause
