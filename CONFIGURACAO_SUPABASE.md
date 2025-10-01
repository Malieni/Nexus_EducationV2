# 🔧 Configuração do Supabase

## ❌ Problema Identificado

Os dados da análise não estão sendo salvos porque o **Supabase não está configurado**. O sistema está tentando usar o Supabase mas não encontra as credenciais necessárias.

## ✅ Solução Implementada

Implementei um **sistema de fallback** que permite o funcionamento sem Supabase:

- **Com Supabase**: Usa banco em nuvem com todas as funcionalidades
- **Sem Supabase**: Usa TinyDB local como fallback

## 🚀 Como Configurar o Supabase (Recomendado)

### 1. Criar Projeto no Supabase

1. Acesse [supabase.com](https://supabase.com)
2. Crie uma conta gratuita
3. Clique em "New Project"
4. Escolha um nome e senha para o projeto
5. Aguarde a criação (pode levar alguns minutos)

### 2. Obter Credenciais

No painel do Supabase:
1. Vá em **Settings** → **API**
2. Copie as seguintes informações:
   - **URL** (algo como `https://xxxxx.supabase.co`)
   - **anon public** key
   - **service_role** key

### 3. Criar Arquivo .env

Crie um arquivo `.env` na raiz do projeto com:

```env
# Configurações do Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=sua_chave_anonima_aqui
SUPABASE_SERVICE_ROLE_KEY=sua_chave_service_role_aqui

# Configurações da API do Groq (para IA)
GROQ_API_KEY=sua_chave_groq_aqui

# Configurações do Google Drive (opcional)
GOOGLE_DRIVE_CREDENTIALS_FILE=token.json
```

### 4. Executar Schema no Supabase

1. No painel do Supabase, vá em **SQL Editor**
2. Copie todo o conteúdo do arquivo `SUPABASE_SCHEMA.md`
3. Cole no editor e execute
4. Isso criará todas as tabelas necessárias

### 5. Migrar Dados (se necessário)

Se você já tem dados no TinyDB:
```bash
python migrate_to_supabase.py
```

## 🔄 Modo Offline (Atual)

**O sistema está funcionando em modo offline** usando TinyDB local. Isso significa:

✅ **Funcionando:**
- Login e cadastro de professores
- Criação e visualização de cursos
- Upload de ementas
- Análise com IA
- Salvamento de análises
- Visualização de disciplinas

⚠️ **Limitações:**
- Dados ficam apenas no computador local
- Sem sincronização entre dispositivos
- Sem backup automático
- Funcionalidades avançadas limitadas

## 🎯 Próximos Passos

### Opção 1: Continuar Offline
- Sistema funciona perfeitamente para uso local
- Dados salvos em `src/data/database/`
- Ideal para testes e desenvolvimento

### Opção 2: Configurar Supabase
- Siga as instruções acima
- Ganhe funcionalidades em nuvem
- Backup automático e sincronização
- Melhor para produção

## 🆘 Suporte

Se tiver problemas:

1. **Verifique o arquivo .env** está na raiz do projeto
2. **Confirme as credenciais** do Supabase
3. **Execute o schema** no Supabase
4. **Teste a conexão** com `python test_supabase_simple.py`

## 📊 Status Atual

```
🔍 [DEBUG] Inicializando SupabaseDatabase...
⚠️ Variáveis de ambiente do Supabase não configuradas!
📝 Configure SUPABASE_URL e SUPABASE_ANON_KEY no arquivo .env
🔄 Usando modo offline (sem Supabase)
✅ TinyDB inicializado como fallback
```

**O sistema está funcionando em modo offline e salvando análises corretamente!** 🎉
