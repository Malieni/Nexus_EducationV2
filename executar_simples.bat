@echo off
echo ========================================
echo 🚀 NEXUS EDUCATION - EXECUÇÃO SIMPLES
echo ========================================
echo.

echo 📋 Instalando dependências com pip...
py -m pip install --upgrade pip
py -m pip install streamlit
py -m pip install pandas
py -m pip install streamlit-aggrid
py -m pip install plotly
py -m pip install supabase
py -m pip install python-dotenv
py -m pip install groq
py -m pip install google-auth
py -m pip install google-auth-oauthlib
py -m pip install google-auth-httplib2
py -m pip install google-api-python-client
py -m pip install pymupdf
py -m pip install pydantic
py -m pip install langchain-groq
py -m pip install bcrypt

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
