# 📚 Integração do Docling - Guia Rápido

## 🎯 O que mudou?

O Nexus Education agora usa **Docling** para extrair dados estruturados de PDFs! Isso significa:

✅ **Extração mais precisa** de informações do aluno  
✅ **Dados estruturados em JSON** salvos no banco  
✅ **Tabelas preservadas** com disciplinas  
✅ **Fallback automático** se Docling falhar  

## 🚀 Instalação

### 1. Instalar Dependências

```bash
# Via Poetry (Recomendado)
poetry install

# Ou via pip
pip install docling
```

### 2. Verificar Instalação

```bash
# Testar se Docling está funcionando
python test_docling.py

# Ou testar com um PDF específico
python test_docling.py caminho/para/seu/arquivo.pdf
```

## 📊 Como Usar

### Na Aplicação Streamlit

1. **Faça login** na aplicação
2. **Selecione um curso**
3. **Faça upload de um PDF** (ementa ou histórico)
4. **Processe a análise**

O sistema irá:
- ✨ Tentar usar Docling para extração estruturada
- ⚠️ Usar PyMuPDF como fallback se necessário
- 💾 Salvar dados estruturados JSON no banco

### No Código

```python
from helper import read_pdf_with_docling

# Extrair dados
pdf_data = read_pdf_with_docling("arquivo.pdf")

# Acessar informações
texto = pdf_data["text"]
dados_estruturados = pdf_data["structured_data"]

# Informações do aluno
aluno = dados_estruturados["student_info"]
nome = aluno.get("nome")
ra = aluno.get("ra")

# Disciplinas
disciplinas = dados_estruturados["disciplines"]
for disc in disciplinas:
    print(f"{disc['nome']} - {disc.get('situacao')}")
```

## 🗄️ Banco de Dados

### Adicionar Coluna no Supabase

Execute a migração SQL:

```sql
-- migrations/add_dados_estruturados_json.sql
ALTER TABLE analises 
ADD COLUMN IF NOT EXISTS dados_estruturados_json TEXT;
```

Ou execute via interface do Supabase:

1. Acesse o **SQL Editor** no Supabase
2. Cole o conteúdo de `migrations/add_dados_estruturados_json.sql`
3. Execute a query

## 📁 Estrutura dos Arquivos Criados

```
Nexus_Education/
├── src/
│   └── core/
│       └── services/
│           └── docling_extractor.py  # Novo: Extrator Docling
├── migrations/
│   └── add_dados_estruturados_json.sql  # Novo: Migração SQL
├── helper.py  # Atualizado: Nova função read_pdf_with_docling()
├── src/app/app.py  # Atualizado: Usa Docling para processar PDFs
├── src/core/models/analise.py  # Atualizado: Campo dados_estruturados_json
├── pyproject.toml  # Atualizado: Dependência do Docling
├── test_docling.py  # Novo: Script de testes
├── DOCLING_INTEGRATION.md  # Novo: Documentação completa
└── README_DOCLING.md  # Este arquivo
```

## 🧪 Testando

### Teste Básico

```bash
python test_docling.py
```

**Saída esperada:**
```
✅ Docling importado com sucesso!
✅ DoclingExtractor criado com sucesso!
✅ Extração concluída!
   Método usado: docling
   Texto extraído: 1234 caracteres
📊 Dados Estruturados:
   - Informações do aluno: True
   - Disciplinas: 15
   - Tabelas: 2
🎉 Todos os testes passaram!
```

### Teste com PDF Específico

```bash
python test_docling.py "src/data/uploads/historico.pdf"
```

## 🔍 Verificando os Dados

### Ver dados extraídos

Após processar um PDF, você pode visualizar os dados estruturados:

```python
from src.core.database.supabase_database import SupabaseDatabase
import json

database = SupabaseDatabase()

# Buscar uma análise
analise = database.client.table("analises").select("*").limit(1).execute()

if analise.data:
    dados_json = analise.data[0].get("dados_estruturados_json")
    if dados_json:
        dados = json.loads(dados_json)
        print(json.dumps(dados, indent=2, ensure_ascii=False))
```

## 📈 Exemplo de Dados Estruturados

```json
{
  "student_info": {
    "nome": "João da Silva",
    "ra": "12345678",
    "curso": "Engenharia de Software",
    "periodo": "8º Semestre"
  },
  "disciplines": [
    {
      "codigo": "ENG001",
      "nome": "Algoritmos e Estruturas de Dados",
      "carga_horaria": "80h",
      "nota": "9.5",
      "situacao": "Aprovado"
    },
    {
      "codigo": "ENG002",
      "nome": "Banco de Dados",
      "carga_horaria": "80h",
      "nota": "8.7",
      "situacao": "Aprovado"
    }
  ],
  "tables": [...],
  "metadata": {...},
  "raw_text": "..."
}
```

## ⚙️ Configuração Avançada

### Personalizar Padrões de Extração

Edite `src/core/services/docling_extractor.py` para adicionar novos padrões:

```python
patterns = {
    "nome": r"(?:Nome(?:\s+Completo)?|Aluno)[:\s]+([^\n]+)",
    "ra": r"(?:RA|Matrícula|Registro)[:\s]+([^\n]+)",
    # Adicione seus padrões aqui
    "email": r"(?:E-mail|Email)[:\s]+([^\n]+)",
    "telefone": r"(?:Tel|Telefone)[:\s]+([^\n]+)",
}
```

## 🐛 Troubleshooting

### Docling não está sendo usado

**Sintoma**: Sistema sempre usa PyMuPDF

**Solução**:
```bash
# Verificar instalação
poetry show docling

# Reinstalar
poetry add docling --force
poetry install
```

### Erro de importação

**Sintoma**: `ImportError: No module named 'docling'`

**Solução**:
```bash
poetry install
# ou
pip install docling
```

### Extração lenta

**Sintoma**: Demora muito para processar

**Solução**: Normal para PDFs grandes. O Docling faz análise estrutural completa.

## 📚 Documentação Completa

Para mais detalhes, consulte:
- `DOCLING_INTEGRATION.md` - Documentação técnica completa
- `src/core/services/docling_extractor.py` - Código do extrator
- [Documentação oficial do Docling](https://github.com/DS4SD/docling)

## 🎓 Benefícios

### Antes (PyMuPDF)
- ❌ Extração básica de texto
- ❌ Sem estrutura
- ❌ Perda de informações de tabelas
- ❌ Regex complexo para extrair dados

### Agora (Docling)
- ✅ Extração estruturada
- ✅ Tabelas preservadas
- ✅ Metadados completos
- ✅ JSON estruturado
- ✅ Dados salvos no banco
- ✅ Análise de IA melhorada

## 🚀 Próximos Passos

1. ✅ Integração básica (CONCLUÍDO)
2. ✅ Extração de dados (CONCLUÍDO)
3. ✅ Armazenamento em JSON (CONCLUÍDO)
4. 🔄 Interface para visualizar dados estruturados (PLANEJADO)
5. 🔄 Exportação de relatórios (PLANEJADO)
6. 🔄 Análise comparativa (PLANEJADO)

## 💡 Dicas

- **Teste com PDFs reais** para ajustar padrões de extração
- **Verifique os logs** no Streamlit para ver qual método foi usado
- **Use o script de teste** para validar novos PDFs
- **Consulte o JSON extraído** para entender a estrutura

## 📞 Suporte

- Verifique `test_docling.py` para diagnóstico
- Consulte `DOCLING_INTEGRATION.md` para detalhes técnicos
- Entre em contato com a equipe de desenvolvimento

---

**🎉 Parabéns! Agora você tem extração inteligente de PDFs com Docling!**

