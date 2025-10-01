# 🎓 Nexus Education

Sistema de Análise de Ementas Acadêmicas com integração ao Google Drive.

## 📁 Estrutura do Projeto

```
Nexus_Education/
├── main.py                    # Ponto de entrada principal
├── pyproject.toml            # Dependências do Poetry
├── poetry.lock               # Lock file das dependências
├── config.env.example        # Exemplo de configurações
├── credentials.json          # Credenciais do Google Drive (você precisa)
├── token.json               # Token de autenticação (gerado automaticamente)
├── db.json                  # Backup do banco antigo
│
├── src/                     # Código fonte principal
│   ├── __init__.py
│   │
│   ├── app/                 # Aplicação Streamlit
│   │   └── app.py          # Interface principal
│   │
│   ├── core/               # Módulos principais
│   │   ├── __init__.py
│   │   │
│   │   ├── database/       # Bancos de dados
│   │   │   ├── __init__.py
│   │   │   ├── database.py           # Banco original (TinyDB único)
│   │   │   └── database_separado.py  # Banco com arquivos separados
│   │   │
│   │   ├── models/         # Modelos de dados (Pydantic)
│   │   │   ├── __init__.py
│   │   │   ├── professor.py
│   │   │   ├── curso.py
│   │   │   ├── disciplinas.py
│   │   │   ├── analise.py
│   │   │   ├── ementa.py
│   │   │   ├── tags.py
│   │   │   ├── professor_curso.py
│   │   │   ├── curso_tags.py
│   │   │   ├── cursos_disciplina.py
│   │   │   └── ementa_disciplina.py
│   │   │
│   │   ├── services/       # Serviços externos
│   │   │   ├── __init__.py
│   │   │   ├── google_drive_service.py  # Integração Google Drive
│   │   │   └── download_ementa.py       # Download de ementas
│   │   │
│   │   └── utils/          # Utilitários e configurações
│   │       ├── __init__.py
│   │       ├── config.py              # Configurações gerais
│   │       └── authenticate.py        # Autenticação
│   │
│   ├── data/               # Dados e arquivos
│   │   ├── database/       # Arquivos JSON do banco
│   │   │   ├── professores.json
│   │   │   ├── cursos.json
│   │   │   ├── disciplinas.json
│   │   │   ├── tags.json
│   │   │   ├── ementas.json
│   │   │   ├── analises.json
│   │   │   ├── professor_curso.json
│   │   │   ├── curso_tags.json
│   │   │   ├── cursos_disciplina.json
│   │   │   └── ementa_disciplina.json
│   │   │
│   │   └── uploads/        # Arquivos enviados pelos usuários
│   │       └── *.pdf       # Ementas e históricos
│   │
│   ├── docs/               # Documentação
│   │   └── GOOGLE_DRIVE_SETUP.md
│   │
│   ├── scripts/            # Scripts auxiliares
│   │   ├── Create_Curso.py
│   │   ├── Create_professor.py
│   │   ├── Create_Curso_com_Tag.py
│   │   └── Create_Curso_Professor_Tag.py
│   │
│   └── tests/              # Testes (futuro)
│       └── (vazio)
│
└── __pycache__/            # Cache Python (gerado automaticamente)
```

## 🚀 Como Executar

### 1. Instalar Dependências
```bash
poetry install
```

### 2. Configurar Supabase
1. Crie um projeto no [Supabase](https://supabase.com)
2. Execute o script SQL do arquivo `SUPABASE_SCHEMA.md` no painel do Supabase
3. Copie as credenciais do projeto
4. Configure as variáveis de ambiente:
```bash
cp config.env.example .env
# Edite o arquivo .env com suas credenciais do Supabase
```

### 3. Migrar Dados (se necessário)
Se você já tem dados no TinyDB, migre para o Supabase:
```bash
poetry run python migrate_to_supabase.py
```

### 4. Configurar Google Drive (Opcional)
1. Siga as instruções em `src/docs/GOOGLE_DRIVE_SETUP.md`
2. Baixe `credentials.json` do Google Cloud Console
3. Coloque na raiz do projeto

### 5. Executar Aplicação
```bash
# Opção 1: Usando o main.py
poetry run python main.py

# Opção 2: Diretamente com Streamlit
poetry run streamlit run src/app/app.py
```

### 6. Acessar
Abra o navegador em: http://localhost:8501

## 🎯 Funcionalidades

### ✅ Implementadas
- **Sistema de Autenticação** (login/cadastro)
- **Cadastro de Professores** com validação
- **Gestão de Cursos e Disciplinas**
- **Upload de PDFs** (1-5 arquivos por lote)
- **Integração com Google Drive** (opcional)
- **Análise de Ementas** (simulada)
- **Tabela Interativa** (AgGrid)
- **Gráficos de Pontuação**
- **Download/Deleção** de arquivos
- **Banco de Dados** com arquivos separados

### 🔄 Em Desenvolvimento
- **Login com Google Auth**
- **Relatórios avançados**
- **Testes automatizados**
- **Internacionalização**

## 🛠️ Tecnologias

- **Python 3.13+**
- **Streamlit** - Interface web
- **Supabase** - Banco de dados em nuvem
- **Pydantic** - Validação de dados
- **AgGrid** - Tabelas interativas
- **Google Drive API** - Armazenamento em nuvem
- **Poetry** - Gerenciamento de dependências

## 📋 Requisitos

- Python 3.13+
- Poetry
- Conta Google (para Google Drive)
- Navegador web moderno

## 🔧 Configuração

### Variáveis de Ambiente
Copie `config.env.example` para `.env` e configure:

```env
DATABASE_PATH=src/data/database
UPLOADS_PATH=src/data/uploads
GOOGLE_DRIVE_FOLDER_ID=seu_folder_id
```

### Google Drive
1. Crie projeto no Google Cloud Console
2. Ative Google Drive API
3. Baixe `credentials.json`
4. Configure `GOOGLE_DRIVE_FOLDER_ID`

## 📚 Documentação

- **Configuração Google Drive**: `src/docs/GOOGLE_DRIVE_SETUP.md`
- **Estrutura de Dados**: `src/core/models/`
- **API Database**: `src/core/database/`

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**Malieni**
- Email: gui.souza.malieni@gmail.com
- GitHub: [@malieni](https://github.com/malieni)

---

**Nexus Education** - Transformando a análise de ementas acadêmicas 🎓