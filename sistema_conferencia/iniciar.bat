@echo off
chcp 65001 >nul
echo ========================================
echo   SISTEMA DE CONFERENCIA NESTLE
echo   INICIANDO SERVIDOR
echo ========================================
echo.

REM Verifica se o ambiente virtual existe
if not exist venv (
    echo ERRO: Ambiente virtual nao encontrado!
    echo.
    echo Execute primeiro o arquivo "instalar.bat" para configurar o sistema.
    echo.
    pause
    exit /b 1
)

echo [1/3] Verificando ambiente virtual...
if not exist venv\Scripts\python.exe (
    echo ERRO: Ambiente virtual corrompido!
    echo.
    echo Execute novamente o arquivo "instalar.bat" para recriar o ambiente.
    echo.
    pause
    exit /b 1
)

echo [2/3] Ativando ambiente virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERRO: Nao foi possivel ativar ambiente virtual.
    pause
    exit /b 1
)

echo [3/3] Iniciando servidor Flask...
echo.
echo ========================================
echo   SERVIDOR INICIADO COM SUCESSO!
echo ========================================
echo.
echo O sistema esta disponivel em:
echo.
echo - Local: http://127.0.0.1:5000
echo - Local: http://localhost:5000
echo.
echo Para acessar de outros computadores na rede:
echo - Rede: http://[SEU-IP]:5000
echo.
echo ========================================
echo   FUNCIONALIDADES DISPONIVEIS:
echo ========================================
echo - Importar base de rastreios
echo - Bipar mercadorias
echo - Aplicar status (Coleta/Insucesso)
echo - Dashboard em tempo real
echo - Exportar relatorios Excel
echo - Visualizar estatisticas
echo.
echo ========================================
echo   CONTROLES:
echo ========================================
echo - Para parar o servidor: CTRL+C
echo - Para reiniciar: Execute este arquivo novamente
echo.
echo Aguardando conexoes...
echo.

python src\main.py

echo.
echo ========================================
echo   SERVIDOR ENCERRADO
echo ========================================
echo.
echo O servidor foi encerrado.
echo Para iniciar novamente, execute este arquivo.
echo.
pause
