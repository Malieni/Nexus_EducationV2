# 🚀 Guia para Teste Local com Poetry

Este guia mostra como configurar e testar o projeto Nexus Education localmente usando Poetry.

## 📋 Pré-requisitos

- Python 3.13+ instalado
- Git instalado
- Conta no Supabase (para banco de dados)
- Conta no Google Cloud Platform (para Google Drive API)

## 🔧 Instalação do Poetry

### Windows (PowerShell)
```powershell
# Instalar Poetry via pip
pip install poetry

# Ou via script oficial (recomendado)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Adicionar Poetry ao PATH (se necessário)
$env:PATH += ";$env:APPDATA\Python\Scripts"
```

### Verificar instalação
```bash
poetry --version
```

## 🛠️ Configuração do Projeto

### 1. Navegar para o diretório do projeto
```bash
cd "C:\Users\User\OneDrive\Área de Trabalho\Nexus_Education"
```

### 2. Instalar dependências
```bash
# Instalar todas as dependências do pyproject.toml
poetry install

# Ou instalar dependências de desenvolvimento também
poetry install --with dev
```

### 3. Configurar variáveis de ambiente
```bash
# Copiar arquivo de exemplo
copy env.example .env

# Editar o arquivo .env com suas credenciais
notepad .env
```

### Conteúdo do arquivo .env:
```env
# Supabase
SUPABASE_URL=sua_url_do_supabase
SUPABASE_ANON_KEY=sua_chave_anonima_do_supabase
SUPABASE_SERVICE_ROLE_KEY=sua_chave_service_role_do_supabase

# Google Drive API
GOOGLE_DRIVE_CREDENTIALS_FILE=token.json

# Groq API (para IA)
GROQ_API_KEY=sua_chave_do_groq

# Configurações do sistema
USE_SUPABASE=true
```

## 🚀 Executar o Projeto

### ⚡ MÉTODO MAIS SIMPLES (Recomendado)

**1. Duplo clique no arquivo `executar_simples.bat`**
- Este script instala todas as dependências automaticamente
- Executa o aplicativo diretamente
- Não precisa configurar Poetry

### 🔧 MÉTODO COM POETRY CORRIGIDO

**Se você quiser usar Poetry (agora corrigido):**

**1. Duplo clique no arquivo `teste_poetry_corrigido.bat`**
- Corrige o formato do pyproject.toml
- Recria o ambiente virtual
- Executa com Poetry

### 📋 Método Manual com Poetry

**Se o Poetry estiver funcionando:**

```bash
# Ativar ambiente virtual do Poetry
py -m poetry shell

# Executar o aplicativo Streamlit
py -m poetry run streamlit run src/app/app.py
```

### 🔧 Método com Scripts Automatizados

**Opção 1: Script Batch (Windows)**
```bash
# Duplo clique em:
executar_local.bat
```

**Opção 2: Script PowerShell**
```powershell
# Execute no PowerShell:
.\executar_local.ps1
```

### 🎯 Execução Direta (sem Poetry)

```bash
# Instalar dependências
py -m pip install -r requirements.txt

# Executar aplicativo
py -m streamlit run src/app/app.py --server.port 8501
```

## 🔍 Verificações Importantes

### 1. Verificar dependências instaladas
```bash
poetry show
```

### 2. Verificar ambiente virtual
```bash
poetry env info
```

### 3. Verificar configuração
```bash
poetry check
```

## 🐛 Solução de Problemas

### Erro: Poetry não encontrado
```bash
# Windows - Adicionar ao PATH
$env:PATH += ";$env:APPDATA\Python\Scripts"

# Ou reinstalar
pip install --user poetry
```

### Erro: Dependências não instaladas
```bash
# Limpar cache e reinstalar
poetry cache clear pypi --all
poetry install --no-cache
```

### Erro: Python 3.13 não encontrado
```bash
# Verificar versão do Python
python --version

# Se necessário, instalar Python 3.13
# Download: https://www.python.org/downloads/
```

### Erro: Módulos não encontrados
```bash
# Verificar se está no ambiente virtual
poetry shell

# Reinstalar dependências
poetry install --force
```

## 📱 Acessar o Aplicativo

Após executar com sucesso:

1. **URL Local**: http://localhost:8501
2. **Interface**: Abrir no navegador
3. **Primeiro uso**: Cadastrar um professor
4. **Testar**: Fazer upload de ementas e análise

## 🔧 Comandos Úteis do Poetry

```bash
# Ver dependências
poetry show

# Adicionar nova dependência
poetry add nome-do-pacote

# Remover dependência
poetry remove nome-do-pacote

# Atualizar dependências
poetry update

# Verificar projeto
poetry check

# Exportar requirements.txt
poetry export -f requirements.txt --output requirements.txt

# Limpar cache
poetry cache clear --all
```

## 📝 Logs e Debug

### Ver logs do Streamlit
```bash
# Executar com logs detalhados
streamlit run src/app/app.py --logger.level debug
```

### Ver logs do Poetry
```bash
# Executar com verbose
poetry run streamlit run src/app/app.py -v
```

## 🎯 Próximos Passos

1. ✅ Configurar variáveis de ambiente
2. ✅ Testar cadastro de professor
3. ✅ Testar upload de ementas
4. ✅ Testar análise com IA
5. ✅ Verificar integração com Supabase
6. ✅ Testar funcionalidades de segurança

## 🆘 Suporte

Se encontrar problemas:

1. Verificar logs do Streamlit
2. Verificar configuração do .env
3. Verificar conexão com Supabase
4. Verificar credenciais do Google Drive
5. Verificar chave da API Groq

---

**🎉 Parabéns! Seu ambiente local está configurado e pronto para desenvolvimento!**
