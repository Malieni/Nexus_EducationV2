@echo off
echo ========================================
echo 🔧 TESTE POETRY CORRIGIDO - NEXUS EDUCATION
echo ========================================
echo.

echo 📋 Verificando Python...
py --version
echo.

echo 📋 Verificando Poetry...
py -m poetry --version
echo.

echo 📋 Navegando para o diretório do projeto...
cd /d "%~dp0"
echo Diretório atual: %CD%
echo.

echo 📋 Verificando configuração do Poetry...
py -m poetry check
echo.

echo 📋 Limpando cache do Poetry...
py -m poetry cache clear --all
echo.

echo 📋 Removendo ambiente virtual antigo (se existir)...
py -m poetry env remove python
echo.

echo 📋 Criando novo ambiente virtual...
py -m poetry install
echo.

echo 📋 Verificando ambiente virtual criado...
py -m poetry env info
echo.

echo 📋 Verificando dependências instaladas...
py -m poetry show
echo.

echo ========================================
echo 🚀 EXECUTANDO O APLICATIVO COM POETRY...
echo ========================================
echo.

echo 📱 Iniciando Streamlit com Poetry...
echo 🌐 O aplicativo será aberto em: http://localhost:8501
echo.
echo ⏹️ Para parar o servidor, pressione Ctrl+C
echo.

py -m poetry run streamlit run src/app/app.py --server.port 8501

echo.
echo ========================================
echo 🎯 APLICAÇÃO FINALIZADA!
echo ========================================
pause
