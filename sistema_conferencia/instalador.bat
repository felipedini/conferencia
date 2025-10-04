@echo off
chcp 65001 >nul
echo ========================================
echo   SISTEMA DE CONFERENCIA NESTLE
echo   INSTALADOR AUTOMATICO
echo ========================================
echo.

echo [1/6] Verificando se o Python esta instalado...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado!
    echo.
    echo Por favor, instale o Python 3.9 ou superior:
    echo https://www.python.org/downloads/
    echo.
    echo Certifique-se de marcar "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b 1
)

echo Python encontrado!
python --version
echo.

echo [2/6] Verificando versao do Python...
python -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"
if %errorlevel% neq 0 (
    echo ERRO: Versao do Python muito antiga!
    echo.
    echo Por favor, instale o Python 3.9 ou superior.
    echo Versao atual: 
    python --version
    echo.
    pause
    exit /b 1
)

echo Versao do Python OK!
echo.

echo [3/6] Removendo ambiente virtual anterior (se existir)...
if exist venv (
    echo Removendo ambiente virtual antigo...
    rmdir /s /q venv
)

echo [4/6] Criando novo ambiente virtual...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERRO: Nao foi possivel criar ambiente virtual.
    echo Certifique-se de que o Python esta instalado corretamente.
    pause
    exit /b 1
)

echo [5/6] Ativando ambiente virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERRO: Nao foi possivel ativar ambiente virtual.
    pause
    exit /b 1
)

echo [6/6] Instalando dependencias...
echo.
echo Instalando Flask e dependencias...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERRO: Falha na instalacao das dependencias.
    echo.
    echo Tentando instalacao manual...
    pip install flask==3.1.1 flask-cors==6.0.0 flask-sqlalchemy==3.1.1 sqlalchemy==2.0.41
    if %errorlevel% neq 0 (
        echo ERRO: Falha na instalacao manual tambem.
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo   INSTALACAO CONCLUIDA COM SUCESSO!
echo ========================================
echo.
echo Dependencias instaladas:
echo - Flask 3.1.1
echo - Flask-CORS 6.0.0  
echo - Flask-SQLAlchemy 3.1.1
echo - SQLAlchemy 2.0.41
echo - Outras dependencias do requirements.txt
echo.
echo Para iniciar o sistema, execute o arquivo "iniciar.bat"
echo.
echo O sistema estara disponivel em:
echo - Local: http://127.0.0.1:5000
echo - Rede: http://[SEU-IP]:5000
echo.
pause
