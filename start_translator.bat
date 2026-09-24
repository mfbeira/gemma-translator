@echo off
echo ===========================================
echo       Carbon Translator - Setup / Run
echo ===========================================
echo.

REM Verifica se o Python esta instalado
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python nao encontrado! Instale o Python e adicione ao PATH.
    pause
    exit /b
)

REM Criando ambiente virtual se nao existir
IF NOT EXIST "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
)

REM Ativando e instalando dependencias
echo Ativando ambiente virtual e verificando dependencias...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo Iniciando a aplicacao Flask...
echo Acesse no seu navegador: http://127.0.0.1:5000
echo Para parar, pressione CTRL+C nesta janela.
echo.

python app.py
pause
