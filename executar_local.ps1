# ========================================
# 🚀 EXECUTANDO NEXUS EDUCATION LOCALMENTE
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚀 EXECUTANDO NEXUS EDUCATION LOCALMENTE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = py --version 2>&1
    Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python não encontrado!" -ForegroundColor Red
    Read-Host "Pressione Enter para sair"
    exit 1
}
Write-Host ""

Write-Host "📋 Verificando Poetry..." -ForegroundColor Yellow
try {
    $poetryVersion = py -m poetry --version 2>&1
    Write-Host "✅ Poetry encontrado: $poetryVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Poetry não encontrado! Instalando..." -ForegroundColor Yellow
    py -m pip install poetry
}
Write-Host ""

Write-Host "📋 Navegando para o diretório do projeto..." -ForegroundColor Yellow
Set-Location $PSScriptRoot
Write-Host "Diretório atual: $(Get-Location)" -ForegroundColor Green
Write-Host ""

Write-Host "📋 Verificando arquivos do projeto..." -ForegroundColor Yellow
if (Test-Path "pyproject.toml") {
    Write-Host "✅ pyproject.toml encontrado" -ForegroundColor Green
} else {
    Write-Host "❌ pyproject.toml não encontrado" -ForegroundColor Red
    Read-Host "Pressione Enter para sair"
    exit 1
}

if (Test-Path "requirements.txt") {
    Write-Host "✅ requirements.txt encontrado" -ForegroundColor Green
} else {
    Write-Host "⚠️ requirements.txt não encontrado" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "📋 Instalando dependências com Poetry..." -ForegroundColor Yellow
try {
    py -m poetry install
    Write-Host "✅ Dependências instaladas com Poetry" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Erro com Poetry, tentando com pip..." -ForegroundColor Yellow
    py -m pip install -r requirements.txt
}
Write-Host ""

Write-Host "📋 Verificando dependências principais..." -ForegroundColor Yellow

# Verificar Streamlit
try {
    $streamlitVersion = py -c "import streamlit; print('Streamlit versão:', streamlit.__version__)" 2>&1
    Write-Host "✅ $streamlitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Streamlit não encontrado! Instalando..." -ForegroundColor Yellow
    py -m pip install streamlit
}

# Verificar Pandas
try {
    $pandasVersion = py -c "import pandas; print('Pandas versão:', pandas.__version__)" 2>&1
    Write-Host "✅ $pandasVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Pandas não encontrado! Instalando..." -ForegroundColor Yellow
    py -m pip install pandas
}

# Verificar st_aggrid
try {
    py -c "import st_aggrid; print('st_aggrid encontrado')" 2>&1
    Write-Host "✅ st_aggrid encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ st_aggrid não encontrado! Instalando..." -ForegroundColor Yellow
    py -m pip install streamlit-aggrid
}

# Verificar Plotly
try {
    py -c "import plotly; print('Plotly encontrado')" 2>&1
    Write-Host "✅ Plotly encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ Plotly não encontrado! Instalando..." -ForegroundColor Yellow
    py -m pip install plotly
}

# Verificar Supabase
try {
    py -c "import supabase; print('Supabase encontrado')" 2>&1
    Write-Host "✅ Supabase encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ Supabase não encontrado! Instalando..." -ForegroundColor Yellow
    py -m pip install supabase
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚀 EXECUTANDO O APLICATIVO..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📱 Iniciando Streamlit..." -ForegroundColor Yellow
Write-Host "🌐 O aplicativo será aberto em: http://localhost:8501" -ForegroundColor Green
Write-Host ""
Write-Host "⏹️ Para parar o servidor, pressione Ctrl+C" -ForegroundColor Yellow
Write-Host ""

try {
    py -m streamlit run src/app/app.py --server.port 8501
} catch {
    Write-Host "❌ Erro ao executar o aplicativo" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🎯 APLICAÇÃO FINALIZADA!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "Pressione Enter para sair"
