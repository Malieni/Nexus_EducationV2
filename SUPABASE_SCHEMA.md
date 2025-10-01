# 🗄️ Schema do Banco de Dados Supabase - Nexus Education

Este documento contém o schema otimizado para migração do TinyDB para Supabase no projeto Nexus Education.

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Configuração do Supabase](#configuração-do-supabase)
3. [Tabelas Principais](#tabelas-principais)
4. [Tabelas de Relacionamento](#tabelas-de-relacionamento)
5. [Row Level Security (RLS)](#row-level-security-rls)
6. [Índices](#índices)
7. [Scripts de Criação](#scripts-de-criação)
8. [Configuração de Autenticação](#configuração-de-autenticação)

---

## 🎯 Visão Geral

O banco de dados foi projetado para funcionar perfeitamente no Supabase com:

- **Integração nativa** com autenticação do Supabase
- **Row Level Security (RLS)** para segurança
- **APIs automáticas** via Supabase
- **Real-time subscriptions** para atualizações em tempo real
- **Storage integrado** para arquivos

---

## ⚙️ Configuração do Supabase

### 1. Criar Projeto no Supabase

1. Acesse [supabase.com](https://supabase.com)
2. Crie um novo projeto
3. Anote as credenciais:
   - **URL do projeto**
   - **API Key (anon)**
   - **API Key (service_role)**

### 2. Configurar Variáveis de Ambiente

```env
# .env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=sua_chave_anonima
SUPABASE_SERVICE_ROLE_KEY=sua_chave_service_role
```

---

## 📊 Tabelas Principais

### 1. **professores**
Armazena dados dos professores do sistema.

```sql
-- Habilitar RLS
ALTER TABLE professores ENABLE ROW LEVEL SECURITY;

CREATE TABLE professores (
    prontuario VARCHAR(9) PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    email_educacional VARCHAR(150) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL, -- Hash da senha
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE, -- Integração com auth
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS Policy: Professores só podem ver/editar seus próprios dados
CREATE POLICY "Professores podem ver seus próprios dados" ON professores
    FOR ALL USING (auth.uid() = user_id);

-- RLS Policy: Professores podem ver outros professores (para listagem)
CREATE POLICY "Professores podem listar outros professores" ON professores
    FOR SELECT USING (true);
```

### 2. **cursos**
Armazena informações dos cursos acadêmicos.

```sql
ALTER TABLE cursos ENABLE ROW LEVEL SECURITY;

CREATE TABLE cursos (
    codigo_curso VARCHAR(50) PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    descricao_curso TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS Policy: Todos podem ver cursos
CREATE POLICY "Todos podem ver cursos" ON cursos
    FOR SELECT USING (true);

-- RLS Policy: Apenas professores autenticados podem modificar
CREATE POLICY "Professores podem modificar cursos" ON cursos
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM professores 
            WHERE user_id = auth.uid()
        )
    );
```

### 3. **disciplinas**
Armazena dados das disciplinas acadêmicas.

```sql
ALTER TABLE disciplinas ENABLE ROW LEVEL SECURITY;

CREATE TABLE disciplinas (
    id_disciplina VARCHAR(15) PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    carga_horaria INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS Policy: Todos podem ver disciplinas
CREATE POLICY "Todos podem ver disciplinas" ON disciplinas
    FOR SELECT USING (true);

-- RLS Policy: Apenas professores podem modificar
CREATE POLICY "Professores podem modificar disciplinas" ON disciplinas
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM professores 
            WHERE user_id = auth.uid()
        )
    );
```

### 4. **tags**
Armazena tags para categorização de cursos.

```sql
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;

CREATE TABLE tags (
    id_tag SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS Policy: Todos podem ver tags
CREATE POLICY "Todos podem ver tags" ON tags
    FOR SELECT USING (true);

-- RLS Policy: Apenas professores podem modificar
CREATE POLICY "Professores podem modificar tags" ON tags
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM professores 
            WHERE user_id = auth.uid()
        )
    );
```

### 5. **ementas**
Armazena informações dos arquivos de ementa.

```sql
ALTER TABLE ementas ENABLE ROW LEVEL SECURITY;

CREATE TABLE ementas (
    id_ementa SERIAL PRIMARY KEY,
    drive_id VARCHAR(255),
    file_path TEXT, -- Caminho no Supabase Storage
    file_name VARCHAR(255),
    file_size BIGINT,
    professor_id VARCHAR(9) REFERENCES professores(prontuario) ON DELETE CASCADE,
    data_upload TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS Policy: Professores só podem ver suas próprias ementas
CREATE POLICY "Professores podem ver suas ementas" ON ementas
    FOR ALL USING (
        professor_id IN (
            SELECT prontuario FROM professores 
            WHERE user_id = auth.uid()
        )
    );
```

### 6. **analises**
Armazena resultados das análises de ementas.

```sql
ALTER TABLE analises ENABLE ROW LEVEL SECURITY;

CREATE TABLE analises (
    analise_id SERIAL PRIMARY KEY,
    nome_aluno VARCHAR(255) NOT NULL,
    ementa_fk INTEGER NOT NULL REFERENCES ementas(id_ementa) ON DELETE CASCADE,
    adequado BOOLEAN NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    texto_analise TEXT NOT NULL,
    materias_restantes TEXT,
    professor_id VARCHAR(9) REFERENCES professores(prontuario) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS Policy: Professores só podem ver suas próprias análises
CREATE POLICY "Professores podem ver suas análises" ON analises
    FOR ALL USING (
        professor_id IN (
            SELECT prontuario FROM professores 
            WHERE user_id = auth.uid()
        )
    );
```

---

## 🔗 Tabelas de Relacionamento

### 1. **professor_curso**
Relaciona professores com cursos (N:N).

```sql
ALTER TABLE professor_curso ENABLE ROW LEVEL SECURITY;

CREATE TABLE professor_curso (
    pc_id SERIAL PRIMARY KEY,
    prontuario_professor VARCHAR(9) NOT NULL REFERENCES professores(prontuario) ON DELETE CASCADE,
    curso_fk VARCHAR(50) NOT NULL REFERENCES cursos(codigo_curso) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(prontuario_professor, curso_fk)
);

-- RLS Policy: Professores só podem ver seus próprios relacionamentos
CREATE POLICY "Professores podem ver seus relacionamentos" ON professor_curso
    FOR ALL USING (
        prontuario_professor IN (
            SELECT prontuario FROM professores 
            WHERE user_id = auth.uid()
        )
    );
```

### 2. **curso_tags**
Relaciona cursos com tags (N:N).

```sql
ALTER TABLE curso_tags ENABLE ROW LEVEL SECURITY;

CREATE TABLE curso_tags (
    ct_id SERIAL PRIMARY KEY,
    curso_fk VARCHAR(50) NOT NULL REFERENCES cursos(codigo_curso) ON DELETE CASCADE,
    tag_fk INTEGER NOT NULL REFERENCES tags(id_tag) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(curso_fk, tag_fk)
);

-- RLS Policy: Todos podem ver relacionamentos curso-tags
CREATE POLICY "Todos podem ver curso-tags" ON curso_tags
    FOR SELECT USING (true);

-- RLS Policy: Apenas professores podem modificar
CREATE POLICY "Professores podem modificar curso-tags" ON curso_tags
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM professores 
            WHERE user_id = auth.uid()
        )
    );
```

### 3. **cursos_disciplina**
Relaciona cursos com disciplinas (N:N).

```sql
ALTER TABLE cursos_disciplina ENABLE ROW LEVEL SECURITY;

CREATE TABLE cursos_disciplina (
    cd_id SERIAL PRIMARY KEY,
    curso_fk VARCHAR(50) NOT NULL REFERENCES cursos(codigo_curso) ON DELETE CASCADE,
    disciplina_fk VARCHAR(15) NOT NULL REFERENCES disciplinas(id_disciplina) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(curso_fk, disciplina_fk)
);

-- RLS Policy: Todos podem ver relacionamentos curso-disciplina
CREATE POLICY "Todos podem ver curso-disciplina" ON cursos_disciplina
    FOR SELECT USING (true);

-- RLS Policy: Apenas professores podem modificar
CREATE POLICY "Professores podem modificar curso-disciplina" ON cursos_disciplina
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM professores 
            WHERE user_id = auth.uid()
        )
    );
```

### 4. **ementa_disciplina**
Relaciona ementas com disciplinas (N:N).

```sql
ALTER TABLE ementa_disciplina ENABLE ROW LEVEL SECURITY;

CREATE TABLE ementa_disciplina (
    ed_id SERIAL PRIMARY KEY,
    ementa_fk INTEGER NOT NULL REFERENCES ementas(id_ementa) ON DELETE CASCADE,
    disciplina_fk VARCHAR(15) NOT NULL REFERENCES disciplinas(id_disciplina) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(ementa_fk, disciplina_fk)
);

-- RLS Policy: Professores só podem ver relacionamentos de suas ementas
CREATE POLICY "Professores podem ver suas ementa-disciplina" ON ementa_disciplina
    FOR ALL USING (
        ementa_fk IN (
            SELECT id_ementa FROM ementas 
            WHERE professor_id IN (
                SELECT prontuario FROM professores 
                WHERE user_id = auth.uid()
            )
        )
    );
```

### 5. **analise_curso**
Relaciona análises com cursos específicos (N:N).

```sql
ALTER TABLE analise_curso ENABLE ROW LEVEL SECURITY;

CREATE TABLE analise_curso (
    ac_id SERIAL PRIMARY KEY,
    analise_fk INTEGER NOT NULL REFERENCES analises(analise_id) ON DELETE CASCADE,
    curso_fk VARCHAR(50) NOT NULL REFERENCES cursos(codigo_curso) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(analise_fk, curso_fk)
);

-- RLS Policy: Professores só podem ver relacionamentos de suas análises
CREATE POLICY "Professores podem ver suas analise-curso" ON analise_curso
    FOR ALL USING (
        analise_fk IN (
            SELECT analise_id FROM analises 
            WHERE professor_id IN (
                SELECT prontuario FROM professores 
                WHERE user_id = auth.uid()
            )
        )
    );
```

---

## 🔐 Row Level Security (RLS)

### Políticas de Segurança

```sql
-- Função para verificar se usuário é professor
CREATE OR REPLACE FUNCTION is_professor()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM professores 
        WHERE user_id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Função para obter prontuário do professor logado
CREATE OR REPLACE FUNCTION get_professor_prontuario()
RETURNS VARCHAR(9) AS $$
BEGIN
    RETURN (
        SELECT prontuario FROM professores 
        WHERE user_id = auth.uid()
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

---

## 🔍 Índices

### Índices para Performance

```sql
-- Índices para consultas frequentes
CREATE INDEX idx_professores_user_id ON professores(user_id);
CREATE INDEX idx_professores_email ON professores(email_educacional);
CREATE INDEX idx_analises_ementa ON analises(ementa_fk);
CREATE INDEX idx_analises_professor ON analises(professor_id);
CREATE INDEX idx_analises_score ON analises(score);
CREATE INDEX idx_analises_adequado ON analises(adequado);
CREATE INDEX idx_ementas_professor ON ementas(professor_id);
CREATE INDEX idx_ementas_data_upload ON ementas(data_upload);

-- Índices para relacionamentos
CREATE INDEX idx_professor_curso_professor ON professor_curso(prontuario_professor);
CREATE INDEX idx_professor_curso_curso ON professor_curso(curso_fk);
CREATE INDEX idx_curso_tags_curso ON curso_tags(curso_fk);
CREATE INDEX idx_curso_tags_tag ON curso_tags(tag_fk);
CREATE INDEX idx_cursos_disciplina_curso ON cursos_disciplina(curso_fk);
CREATE INDEX idx_cursos_disciplina_disciplina ON cursos_disciplina(disciplina_fk);
CREATE INDEX idx_ementa_disciplina_ementa ON ementa_disciplina(ementa_fk);
CREATE INDEX idx_ementa_disciplina_disciplina ON ementa_disciplina(disciplina_fk);
```

---

## 🚀 Scripts de Criação

### Script Completo para Supabase

```sql
-- ========================================
-- NEXUS EDUCATION - SCHEMA SUPABASE
-- ========================================

-- Habilitar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- FUNÇÕES AUXILIARES
-- ========================================

-- Função para verificar se usuário é professor
CREATE OR REPLACE FUNCTION is_professor()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM professores 
        WHERE user_id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Função para obter prontuário do professor logado
CREATE OR REPLACE FUNCTION get_professor_prontuario()
RETURNS VARCHAR(9) AS $$
BEGIN
    RETURN (
        SELECT prontuario FROM professores 
        WHERE user_id = auth.uid()
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Função para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- TABELAS PRINCIPAIS
-- ========================================

-- Professores
CREATE TABLE professores (
    prontuario VARCHAR(9) PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    email_educacional VARCHAR(150) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT chk_professores_prontuario CHECK (prontuario ~ '^[0-9]{9}$'),
    CONSTRAINT chk_professores_email CHECK (email_educacional ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Cursos
CREATE TABLE cursos (
    codigo_curso VARCHAR(50) PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    descricao_curso TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Disciplinas
CREATE TABLE disciplinas (
    id_disciplina VARCHAR(15) PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    carga_horaria INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tags
CREATE TABLE tags (
    id_tag SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ementas
CREATE TABLE ementas (
    id_ementa SERIAL PRIMARY KEY,
    drive_id VARCHAR(255),
    file_path TEXT,
    file_name VARCHAR(255),
    file_size BIGINT,
    professor_id VARCHAR(9) REFERENCES professores(prontuario) ON DELETE CASCADE,
    data_upload TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Análises
CREATE TABLE analises (
    analise_id SERIAL PRIMARY KEY,
    nome_aluno VARCHAR(255) NOT NULL,
    ementa_fk INTEGER NOT NULL REFERENCES ementas(id_ementa) ON DELETE CASCADE,
    adequado BOOLEAN NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    texto_analise TEXT NOT NULL,
    materias_restantes TEXT,
    professor_id VARCHAR(9) REFERENCES professores(prontuario) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- TABELAS DE RELACIONAMENTO
-- ========================================

-- Professor_Curso
CREATE TABLE professor_curso (
    pc_id SERIAL PRIMARY KEY,
    prontuario_professor VARCHAR(9) NOT NULL REFERENCES professores(prontuario) ON DELETE CASCADE,
    curso_fk VARCHAR(50) NOT NULL REFERENCES cursos(codigo_curso) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(prontuario_professor, curso_fk)
);

-- Curso_Tags
CREATE TABLE curso_tags (
    ct_id SERIAL PRIMARY KEY,
    curso_fk VARCHAR(50) NOT NULL REFERENCES cursos(codigo_curso) ON DELETE CASCADE,
    tag_fk INTEGER NOT NULL REFERENCES tags(id_tag) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(curso_fk, tag_fk)
);

-- Cursos_Disciplina
CREATE TABLE cursos_disciplina (
    cd_id SERIAL PRIMARY KEY,
    curso_fk VARCHAR(50) NOT NULL REFERENCES cursos(codigo_curso) ON DELETE CASCADE,
    disciplina_fk VARCHAR(15) NOT NULL REFERENCES disciplinas(id_disciplina) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(curso_fk, disciplina_fk)
);

-- Ementa_Disciplina
CREATE TABLE ementa_disciplina (
    ed_id SERIAL PRIMARY KEY,
    ementa_fk INTEGER NOT NULL REFERENCES ementas(id_ementa) ON DELETE CASCADE,
    disciplina_fk VARCHAR(15) NOT NULL REFERENCES disciplinas(id_disciplina) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(ementa_fk, disciplina_fk)
);

-- Analise_Curso
CREATE TABLE analise_curso (
    ac_id SERIAL PRIMARY KEY,
    analise_fk INTEGER NOT NULL REFERENCES analises(analise_id) ON DELETE CASCADE,
    curso_fk VARCHAR(50) NOT NULL REFERENCES cursos(codigo_curso) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(analise_fk, curso_fk)
);

-- ========================================
-- ÍNDICES
-- ========================================

-- Índices para consultas frequentes
CREATE INDEX idx_professores_user_id ON professores(user_id);
CREATE INDEX idx_professores_email ON professores(email_educacional);
CREATE INDEX idx_analises_ementa ON analises(ementa_fk);
CREATE INDEX idx_analises_professor ON analises(professor_id);
CREATE INDEX idx_analises_score ON analises(score);
CREATE INDEX idx_analises_adequado ON analises(adequado);
CREATE INDEX idx_ementas_professor ON ementas(professor_id);
CREATE INDEX idx_ementas_data_upload ON ementas(data_upload);

-- Índices para relacionamentos
CREATE INDEX idx_professor_curso_professor ON professor_curso(prontuario_professor);
CREATE INDEX idx_professor_curso_curso ON professor_curso(curso_fk);
CREATE INDEX idx_curso_tags_curso ON curso_tags(curso_fk);
CREATE INDEX idx_curso_tags_tag ON curso_tags(tag_fk);
CREATE INDEX idx_cursos_disciplina_curso ON cursos_disciplina(curso_fk);
CREATE INDEX idx_cursos_disciplina_disciplina ON cursos_disciplina(disciplina_fk);
CREATE INDEX idx_ementa_disciplina_ementa ON ementa_disciplina(ementa_fk);
CREATE INDEX idx_ementa_disciplina_disciplina ON ementa_disciplina(disciplina_fk);
CREATE INDEX idx_analise_curso_analise ON analise_curso(analise_fk);
CREATE INDEX idx_analise_curso_curso ON analise_curso(curso_fk);

-- ========================================
-- ROW LEVEL SECURITY
-- ========================================

-- Habilitar RLS em todas as tabelas
ALTER TABLE professores ENABLE ROW LEVEL SECURITY;
ALTER TABLE cursos ENABLE ROW LEVEL SECURITY;
ALTER TABLE disciplinas ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE ementas ENABLE ROW LEVEL SECURITY;
ALTER TABLE analises ENABLE ROW LEVEL SECURITY;
ALTER TABLE professor_curso ENABLE ROW LEVEL SECURITY;
ALTER TABLE curso_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE cursos_disciplina ENABLE ROW LEVEL SECURITY;
ALTER TABLE ementa_disciplina ENABLE ROW LEVEL SECURITY;
ALTER TABLE analise_curso ENABLE ROW LEVEL SECURITY;

-- Políticas RLS
CREATE POLICY "Professores podem ver seus próprios dados" ON professores
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Professores podem listar outros professores" ON professores
    FOR SELECT USING (true);

CREATE POLICY "Todos podem ver cursos" ON cursos
    FOR SELECT USING (true);

CREATE POLICY "Professores podem modificar cursos" ON cursos
    FOR ALL USING (is_professor());

CREATE POLICY "Todos podem ver disciplinas" ON disciplinas
    FOR SELECT USING (true);

CREATE POLICY "Professores podem modificar disciplinas" ON disciplinas
    FOR ALL USING (is_professor());

CREATE POLICY "Todos podem ver tags" ON tags
    FOR SELECT USING (true);

CREATE POLICY "Professores podem modificar tags" ON tags
    FOR ALL USING (is_professor());

CREATE POLICY "Professores podem ver suas ementas" ON ementas
    FOR ALL USING (
        professor_id IN (
            SELECT prontuario FROM professores 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Professores podem ver suas análises" ON analises
    FOR ALL USING (
        professor_id IN (
            SELECT prontuario FROM professores 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Professores podem ver seus relacionamentos" ON professor_curso
    FOR ALL USING (
        prontuario_professor IN (
            SELECT prontuario FROM professores 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Todos podem ver curso-tags" ON curso_tags
    FOR SELECT USING (true);

CREATE POLICY "Professores podem modificar curso-tags" ON curso_tags
    FOR ALL USING (is_professor());

CREATE POLICY "Todos podem ver curso-disciplina" ON cursos_disciplina
    FOR SELECT USING (true);

CREATE POLICY "Professores podem modificar curso-disciplina" ON cursos_disciplina
    FOR ALL USING (is_professor());

CREATE POLICY "Professores podem ver suas ementa-disciplina" ON ementa_disciplina
    FOR ALL USING (
        ementa_fk IN (
            SELECT id_ementa FROM ementas 
            WHERE professor_id IN (
                SELECT prontuario FROM professores 
                WHERE user_id = auth.uid()
            )
        )
    );

CREATE POLICY "Professores podem ver suas analise-curso" ON analise_curso
    FOR ALL USING (
        analise_fk IN (
            SELECT analise_id FROM analises 
            WHERE professor_id IN (
                SELECT prontuario FROM professores 
                WHERE user_id = auth.uid()
            )
        )
    );

-- ========================================
-- TRIGGERS
-- ========================================

-- Triggers para updated_at
CREATE TRIGGER update_professores_updated_at 
    BEFORE UPDATE ON professores 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cursos_updated_at 
    BEFORE UPDATE ON cursos 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_disciplinas_updated_at 
    BEFORE UPDATE ON disciplinas 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analises_updated_at 
    BEFORE UPDATE ON analises 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- COMENTÁRIOS
-- ========================================

COMMENT ON DATABASE postgres IS 'Banco de dados do sistema Nexus Education - Análise de Ementas Acadêmicas (Supabase)';
COMMENT ON TABLE professores IS 'Tabela de professores do sistema com integração ao auth.users';
COMMENT ON TABLE cursos IS 'Tabela de cursos acadêmicos';
COMMENT ON TABLE disciplinas IS 'Tabela de disciplinas acadêmicas';
COMMENT ON TABLE tags IS 'Tabela de tags para categorização';
COMMENT ON TABLE ementas IS 'Tabela de arquivos de ementa com integração ao Storage';
COMMENT ON TABLE analises IS 'Tabela de resultados de análises';
COMMENT ON TABLE professor_curso IS 'Relacionamento N:N entre professores e cursos';
COMMENT ON TABLE curso_tags IS 'Relacionamento N:N entre cursos e tags';
COMMENT ON TABLE cursos_disciplina IS 'Relacionamento N:N entre cursos e disciplinas';
COMMENT ON TABLE ementa_disciplina IS 'Relacionamento N:N entre ementas e disciplinas';
COMMENT ON TABLE analise_curso IS 'Relacionamento N:N entre análises e cursos';
```

---

## 🔐 Configuração de Autenticação

### 1. Configurar Supabase Auth

```sql
-- Configurar políticas de autenticação
-- (Isso é feito no painel do Supabase)

-- Exemplo de configuração no painel:
-- 1. Vá para Authentication > Settings
-- 2. Configure "Site URL" para sua aplicação
-- 3. Configure "Redirect URLs" se necessário
-- 4. Ative "Enable email confirmations" se desejado
```

### 2. Configurar Storage

```sql
-- Criar bucket para ementas
INSERT INTO storage.buckets (id, name, public) 
VALUES ('ementas', 'ementas', false);

-- Política para upload de ementas
CREATE POLICY "Professores podem uploadar ementas" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'ementas' AND
        auth.uid() IN (
            SELECT user_id FROM professores
        )
    );

-- Política para visualizar ementas
CREATE POLICY "Professores podem ver suas ementas" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'ementas' AND
        auth.uid() IN (
            SELECT user_id FROM professores
        )
    );

-- Política para deletar ementas
CREATE POLICY "Professores podem deletar suas ementas" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'ementas' AND
        auth.uid() IN (
            SELECT user_id FROM professores
        )
    );
```

---

## 🐍 Código Python para Supabase

### 1. Instalar Dependências

```bash
pip install supabase
```

### 2. Configurar Cliente

```python
# config/supabase.py
from supabase import create_client, Client
import os

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(url, key)
```

### 3. Exemplo de Uso

```python
# services/professor_service.py
from config.supabase import supabase

class ProfessorService:
    @staticmethod
    def get_professor_by_email(email: str):
        response = supabase.table("professores").select("*").eq("email_educacional", email).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def create_professor(professor_data: dict):
        response = supabase.table("professores").insert(professor_data).execute()
        return response.data[0]
    
    @staticmethod
    def get_analises_by_professor(prontuario: str):
        response = supabase.table("analises").select("*").eq("professor_id", prontuario).execute()
        return response.data
```

---

## 📊 Queries Úteis para Supabase

### 1. Consultas com Joins

```sql
-- Análises com informações do professor e ementa
SELECT 
    a.analise_id,
    a.nome_aluno,
    a.score,
    a.adequado,
    p.nome as professor_nome,
    e.file_name as ementa_nome
FROM analises a
JOIN professores p ON a.professor_id = p.prontuario
JOIN ementas e ON a.ementa_fk = e.id_ementa
WHERE p.user_id = auth.uid();
```

### 2. Estatísticas

```sql
-- Estatísticas de análises por professor
SELECT 
    p.nome,
    COUNT(a.analise_id) as total_analises,
    AVG(a.score) as media_score,
    COUNT(CASE WHEN a.adequado = true THEN 1 END) as adequadas
FROM professores p
LEFT JOIN analises a ON p.prontuario = a.professor_id
WHERE p.user_id = auth.uid()
GROUP BY p.prontuario, p.nome;
```

### 3. Análises por Curso

```sql
-- Análises de um professor filtradas por curso específico
SELECT 
    a.analise_id,
    a.nome_aluno,
    a.score,
    a.adequado,
    a.texto_analise,
    a.materias_restantes,
    c.nome as curso_nome,
    c.codigo_curso,
    e.file_name as ementa_nome,
    a.created_at
FROM analises a
JOIN analise_curso ac ON a.analise_id = ac.analise_fk
JOIN cursos c ON ac.curso_fk = c.codigo_curso
JOIN ementas e ON a.ementa_fk = e.id_ementa
WHERE a.professor_id IN (
    SELECT prontuario FROM professores 
    WHERE user_id = auth.uid()
)
AND c.codigo_curso = 'CODIGO_DO_CURSO_AQUI'
ORDER BY a.created_at DESC;
```

### 4. Estatísticas por Curso

```sql
-- Estatísticas de análises por curso para um professor
SELECT 
    c.codigo_curso,
    c.nome as curso_nome,
    COUNT(a.analise_id) as total_analises,
    AVG(a.score) as media_score,
    COUNT(CASE WHEN a.adequado = true THEN 1 END) as adequadas,
    COUNT(CASE WHEN a.adequado = false THEN 1 END) as inadequadas
FROM cursos c
JOIN analise_curso ac ON c.codigo_curso = ac.curso_fk
JOIN analises a ON ac.analise_fk = a.analise_id
WHERE a.professor_id IN (
    SELECT prontuario FROM professores 
    WHERE user_id = auth.uid()
)
GROUP BY c.codigo_curso, c.nome
ORDER BY total_analises DESC;
```

### 5. Cursos com Análises

```sql
-- Listar todos os cursos que têm análises para um professor
SELECT DISTINCT
    c.codigo_curso,
    c.nome as curso_nome,
    c.descricao_curso,
    COUNT(a.analise_id) as total_analises
FROM cursos c
JOIN analise_curso ac ON c.codigo_curso = ac.curso_fk
JOIN analises a ON ac.analise_fk = a.analise_id
WHERE a.professor_id IN (
    SELECT prontuario FROM professores 
    WHERE user_id = auth.uid()
)
GROUP BY c.codigo_curso, c.nome, c.descricao_curso
ORDER BY c.nome;
```

### 6. Análise Completa com Relacionamentos

```sql
-- Análise completa com todos os relacionamentos
SELECT 
    a.analise_id,
    a.nome_aluno,
    a.score,
    a.adequado,
    a.texto_analise,
    a.materias_restantes,
    p.nome as professor_nome,
    c.nome as curso_nome,
    c.codigo_curso,
    e.file_name as ementa_nome,
    e.data_upload,
    a.created_at
FROM analises a
JOIN professores p ON a.professor_id = p.prontuario
JOIN analise_curso ac ON a.analise_id = ac.analise_fk
JOIN cursos c ON ac.curso_fk = c.codigo_curso
JOIN ementas e ON a.ementa_fk = e.id_ementa
WHERE p.user_id = auth.uid()
ORDER BY a.created_at DESC;
```

---

## 🚀 Deploy e Configuração

### 1. Configurar Variáveis de Ambiente

```env
# .env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=sua_chave_anonima
SUPABASE_SERVICE_ROLE_KEY=sua_chave_service_role
```

### 2. Atualizar Código da Aplicação

```python
# Substituir TinyDB por Supabase
# Exemplo: src/core/database/supabase_database.py

from supabase import create_client, Client
from typing import List, Dict, Optional

class SupabaseDatabase:
    def __init__(self):
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
    
    def get_professor_by_email(self, email: str) -> Optional[Dict]:
        response = self.supabase.table("professores").select("*").eq("email_educacional", email).execute()
        return response.data[0] if response.data else None
```

---

## ✅ Checklist de Migração para Supabase

- [x] Criar projeto no Supabase
- [x] Executar script de criação das tabelas
- [x] Configurar RLS policies
- [x] Configurar Storage para arquivos
- [x] Configurar autenticação
- [x] Migrar dados do TinyDB
- [x] Atualizar código da aplicação
- [ ] Testar integração completa
- [ ] Configurar backup automático
- [ ] Deploy em produção

---

## 🆘 Suporte

Para dúvidas sobre a implementação no Supabase:

- [Documentação Supabase](https://supabase.com/docs)
- [Guia de RLS](https://supabase.com/docs/guides/auth/row-level-security)
- [Python Client](https://supabase.com/docs/reference/python)

---

**Criado em:** $(date)  
**Versão:** 1.0  
**Autor:** Sistema Nexus Education  
**Plataforma:** Supabase
