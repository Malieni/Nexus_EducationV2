# 📁 Estrutura do Projeto Nexus Education

## 🎯 Organização Profissional

O projeto foi reorganizado seguindo as melhores práticas de desenvolvimento Python, com separação clara de responsabilidades e estrutura modular.

## 📂 Estrutura de Diretórios

### 🏗️ **Arquitetura Principal**

```
Nexus_Education/
├── 📄 Arquivos de Configuração
│   ├── main.py                 # Ponto de entrada principal
│   ├── run.py                  # Script de inicialização
│   ├── pyproject.toml          # Dependências Poetry
│   ├── poetry.lock             # Lock file
│   ├── config.env.example      # Exemplo de configurações
│   └── README.md               # Documentação principal
│
├── 🎨 Configuração Streamlit
│   └── .streamlit/
│       └── config.toml         # Configurações do Streamlit
│
├── 📦 Código Fonte (src/)
│   ├── __init__.py
│   │
│   ├── 🖥️ app/                 # Aplicação Principal
│   │   └── app.py             # Interface Streamlit
│   │
│   ├── ⚙️ core/               # Módulos Principais
│   │   ├── __init__.py
│   │   │
│   │   ├── 🗄️ database/       # Camada de Dados
│   │   │   ├── __init__.py
│   │   │   ├── database.py           # Banco original
│   │   │   └── database_separado.py  # Banco com arquivos separados
│   │   │
│   │   ├── 📋 models/         # Modelos de Dados
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
│   │   ├── 🔌 services/       # Serviços Externos
│   │   │   ├── __init__.py
│   │   │   ├── google_drive_service.py
│   │   │   └── download_ementa.py
│   │   │
│   │   └── 🛠️ utils/          # Utilitários
│   │       ├── __init__.py
│   │       ├── config.py
│   │       └── authenticate.py
│   │
│   ├── 💾 data/               # Dados e Arquivos
│   │   ├── database/          # Arquivos JSON do banco
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
│   │   └── uploads/           # Arquivos enviados
│   │       └── *.pdf          # Ementas e históricos
│   │
│   ├── 📚 docs/               # Documentação
│   │   ├── ESTRUTURA_PROJETO.md
│   │   └── GOOGLE_DRIVE_SETUP.md
│   │
│   ├── 🔧 scripts/            # Scripts Auxiliares
│   │   ├── Create_Curso.py
│   │   ├── Create_professor.py
│   │   ├── Create_Curso_com_Tag.py
│   │   └── Create_Curso_Professor_Tag.py
│   │
│   └── 🧪 tests/              # Testes (futuro)
│       └── (vazio)
│
└── 🔐 Arquivos de Credenciais
    ├── credentials.json       # Google Drive (você precisa)
    └── token.json            # Token de autenticação (gerado)
```

## 🎯 **Princípios de Organização**

### 1. **Separação de Responsabilidades**
- **`app/`**: Interface do usuário (Streamlit)
- **`core/`**: Lógica de negócio e funcionalidades
- **`data/`**: Dados e arquivos
- **`docs/`**: Documentação
- **`scripts/`**: Utilitários e scripts

### 2. **Modularidade**
- Cada módulo tem responsabilidade específica
- Imports organizados e claros
- Dependências bem definidas

### 3. **Escalabilidade**
- Estrutura preparada para crescimento
- Fácil adição de novos módulos
- Testes separados

### 4. **Manutenibilidade**
- Código organizado e legível
- Documentação clara
- Configurações centralizadas

## 🔄 **Fluxo de Dados**

```
Interface (app/) 
    ↓
Lógica (core/)
    ↓
Dados (data/)
    ↓
Serviços Externos (services/)
```

## 📋 **Convenções de Nomenclatura**

### **Arquivos Python**
- `snake_case.py` para arquivos
- `PascalCase` para classes
- `snake_case` para funções e variáveis

### **Diretórios**
- `snake_case/` para pastas
- `__init__.py` em cada pacote

### **JSON**
- `snake_case.json` para arquivos de dados
- Chaves em `snake_case`

## 🚀 **Como Executar**

### **Opção 1: Script de Inicialização**
```bash
python run.py
```

### **Opção 2: Main.py**
```bash
poetry run python main.py
```

### **Opção 3: Streamlit Direto**
```bash
poetry run streamlit run src/app/app.py
```

## 🔧 **Configuração**

### **Variáveis de Ambiente**
Copie `config.env.example` para `.env`:
```env
DATABASE_PATH=src/data/database
UPLOADS_PATH=src/data/uploads
GOOGLE_DRIVE_FOLDER_ID=seu_folder_id
```

### **Streamlit**
Configurações em `.streamlit/config.toml`

## 📚 **Documentação**

- **README.md**: Visão geral do projeto
- **ESTRUTURA_PROJETO.md**: Esta documentação
- **GOOGLE_DRIVE_SETUP.md**: Configuração do Google Drive

## 🎯 **Vantagens da Nova Estrutura**

1. **Organização Profissional**: Segue padrões da indústria
2. **Manutenibilidade**: Fácil de manter e expandir
3. **Escalabilidade**: Preparada para crescimento
4. **Clareza**: Cada arquivo tem propósito específico
5. **Modularidade**: Componentes independentes
6. **Testabilidade**: Estrutura preparada para testes

## 🔄 **Migração Realizada**

- ✅ **Arquivos reorganizados** por funcionalidade
- ✅ **Imports atualizados** para nova estrutura
- ✅ **Caminhos corrigidos** para dados e uploads
- ✅ **Documentação criada** para nova estrutura
- ✅ **Scripts de inicialização** adicionados
- ✅ **Configurações centralizadas**

---

**Nexus Education** - Estrutura profissional e organizada! 🎓
