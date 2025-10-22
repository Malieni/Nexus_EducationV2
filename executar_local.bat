@echo off
echo ========================================
echo 🚀 EXECUTANDO NEXUS EDUCATION LOCALMENTE
echo ========================================
echo.

echo 📋 Verificando Python...
py --version
if %errorlevel% neq 0 (
    echo ❌ Python não encontrado!
    pause
    exit /b 1
)
echo.

echo 📋 Verificando Poetry...
py -m poetry --version
if %errorlevel% neq 0 (
    echo ❌ Poetry não encontrado! Instalando...
    py -m pip install poetry
)
echo.

echo 📋 Navegando para o diretório do projeto...
cd /d "%~dp0"
echo Diretório atual: %CD%
echo.

echo 📋 Verificando arquivos do projeto...
if exist "pyproject.toml" (
    echo ✅ pyproject.toml encontrado
) else (
    echo ❌ pyproject.toml não encontrado
    pause
    exit /b 1
)

if exist "requirements.txt" (
    echo ✅ requirements.txt encontrado
) else (
    echo ⚠️ requirements.txt não encontrado
)

echo.
echo 📋 Instalando dependências com Poetry...
py -m poetry install
if %errorlevel% neq 0 (
    echo ⚠️ Erro com Poetry, tentando com pip...
    py -m pip install -r requirements.txt
)
echo.

echo 📋 Verificando se Streamlit está instalado...
py -c "import streamlit; print('Streamlit versão:', streamlit.__version__)"
if %errorlevel% neq 0 (
    echo ❌ Streamlit não encontrado! Instalando...
    py -m pip install streamlit
)

echo.
echo 📋 Verificando se pandas está instalado...
py -c "import pandas; print('Pandas versão:', pandas.__version__)"
if %errorlevel% neq 0 (
    echo ❌ Pandas não encontrado! Instalando...
    py -m pip install pandas
)

echo.
echo 📋 Verificando se st_aggrid está instalado...
py -c "import st_aggrid; print('st_aggrid encontrado')"
if %errorlevel% neq 0 (
    echo ❌ st_aggrid não encontrado! Instalando...
    py -m pip install streamlit-aggrid
)

echo.
echo 📋 Verificando se plotly está instalado...
py -c "import plotly; print('Plotly encontrado')"
if %errorlevel% neq 0 (
    echo ❌ Plotly não encontrado! Instalando...
    py -m pip install plotly
)

echo.
echo 📋 Verificando se supabase está instalado...
py -c "import supabase; print('Supabase encontrado')"
if %errorlevel% neq 0 (
    echo ❌ Supabase não encontrado! Instalando...
    py -m pip install supabase
)

echo.
echo ========================================
echo 🚀 EXECUTANDO O APLICATIVO...
echo ========================================
echo.

echo 📱 Iniciando Streamlit...
echo 🌐 O aplicativo será aberto em: http://localhost:8501
echo.
echo ⏹️ Para parar o servidor, pressione Ctrl+C
echo.

py -m streamlit run src/app/app.py --server.port 8501

echo.
echo ========================================
echo 🎯 APLICAÇÃO FINALIZADA!
echo ========================================
pause
