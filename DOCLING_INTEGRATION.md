# Integração com Docling

## Visão Geral

O Nexus Education agora utiliza o **Docling** para extrair dados estruturados de PDFs de forma inteligente. O Docling transforma PDFs em dados JSON estruturados, permitindo melhor análise e armazenamento das informações.

## O que é Docling?

Docling é uma biblioteca avançada de extração de documentos que:
- Extrai texto de forma mais precisa que métodos tradicionais
- Identifica e extrai tabelas estruturadas
- Reconhece seções e hierarquias do documento
- Preserva metadados importantes
- Exporta dados em formato JSON estruturado

## Instalação

### Via Poetry (Recomendado)

```bash
poetry install
```

### Via pip

```bash
pip install docling
```

## Como Funciona

### 1. Processamento de PDF

Quando um PDF é enviado, o sistema:

1. **Tenta usar Docling primeiro** para extração estruturada
2. **Fallback para PyMuPDF** se Docling falhar
3. **Extrai dados estruturados**:
   - Informações do aluno (nome, RA, curso, período)
   - Disciplinas cursadas (código, nome, carga horária, nota, situação)
   - Tabelas completas
   - Metadados do documento
   - Seções organizadas

### 2. Estrutura dos Dados Extraídos

O Docling retorna um JSON com a seguinte estrutura:

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
    }
  ],
  "tables": [
    {
      "headers": ["Código", "Disciplina", "CH", "Nota"],
      "rows": [...]
    }
  ],
  "metadata": {},
  "sections": [],
  "raw_text": "..."
}
```

### 3. Armazenamento no Banco de Dados

Os dados estruturados são salvos na tabela `analises` no campo `dados_estruturados_json`:

```sql
ALTER TABLE analises 
ADD COLUMN dados_estruturados_json TEXT;
```

## Uso na Aplicação

### No Código

```python
from helper import read_pdf_with_docling

# Extrair dados estruturados
pdf_data = read_pdf_with_docling("caminho/para/arquivo.pdf")

# Acessar dados
texto = pdf_data["text"]
structured_data = pdf_data["structured_data"]
method = pdf_data["method"]  # "docling" ou "pymupdf_fallback"

# Extrair informações específicas
student_info = structured_data["student_info"]
nome_aluno = student_info.get("nome", "Não identificado")
disciplines = structured_data["disciplines"]
```

### Na Interface Streamlit

O sistema exibe automaticamente qual método foi usado:
- ✨ **"Usando Docling para extração estruturada"** - Sucesso
- ⚠️ **"Docling falhou, usando PyMuPDF"** - Fallback

## Vantagens do Docling

### Comparado ao PyMuPDF Tradicional

| Aspecto | PyMuPDF | Docling |
|---------|---------|---------|
| Extração de Texto | Básica | Avançada |
| Tabelas | Não | ✅ Sim |
| Estrutura | Não | ✅ Sim |
| Metadados | Limitado | ✅ Completo |
| JSON Estruturado | Não | ✅ Sim |
| Performance | Rápida | Moderada |

### Benefícios para o Projeto

1. **Melhor Precisão**: Extração mais precisa de informações do aluno
2. **Dados Estruturados**: Facilita análise e processamento
3. **Tabelas Preservadas**: Disciplinas em formato tabular
4. **Escalabilidade**: Fácil adicionar novos campos
5. **IA Melhorada**: Dados estruturados melhoram análise da IA

## Configuração Avançada

### Personalizar Extrator

```python
from src.core.services.docling_extractor import DoclingExtractor

extractor = DoclingExtractor()

# Processar PDF
structured_data = extractor.process_pdf_to_json("arquivo.pdf")

# Extrair informações específicas
student_info = extractor.extract_student_info(structured_data)
disciplines = extractor.extract_disciplines(structured_data)

# Salvar em JSON
extractor.save_to_json_file(structured_data, "output.json")
```

### Adicionar Novos Padrões de Extração

Edite `src/core/services/docling_extractor.py`:

```python
def extract_student_info(self, document_data: Dict) -> Dict:
    patterns = {
        "nome": r"(?:Nome(?:\s+Completo)?|Aluno)[:\s]+([^\n]+)",
        "ra": r"(?:RA|Matrícula|Registro)[:\s]+([^\n]+)",
        # Adicione novos padrões aqui
        "email": r"(?:E-mail|Email)[:\s]+([^\n]+)",
    }
    # ...
```

## Troubleshooting

### Docling não está sendo usado

**Problema**: Sistema sempre usa PyMuPDF

**Solução**:
```bash
# Verificar se está instalado
poetry show docling

# Reinstalar se necessário
poetry add docling

# Verificar no código
python -c "from src.core.services.docling_extractor import DoclingExtractor; print('OK')"
```

### Erro ao importar Docling

**Problema**: `ImportError: No module named 'docling'`

**Solução**:
```bash
# Atualizar dependências
poetry install --no-root

# Ou instalar diretamente
pip install docling
```

### Extração lenta

**Problema**: Docling demora muito para processar

**Solução**:
- PDFs grandes podem demorar mais
- Considere usar PyMuPDF para PDFs simples
- Configure timeout se necessário

## Migração de Dados

### Reprocessar Análises Antigas

Para adicionar dados estruturados às análises já existentes:

```python
from src.core.database.supabase_database import SupabaseDatabase
from helper import read_pdf_with_docling
import json

database = SupabaseDatabase()

# Buscar análises sem dados estruturados
analises = database.client.table("analises").select("*").is_("dados_estruturados_json", "null").execute()

for analise in analises.data:
    ementa_id = analise["ementa_fk"]
    # Buscar PDF da ementa
    # Processar com Docling
    # Atualizar análise
```

## Schema do Banco de Dados

### Adicionar Campo no Supabase

```sql
-- Adicionar coluna para dados estruturados
ALTER TABLE analises 
ADD COLUMN IF NOT EXISTS dados_estruturados_json TEXT;

-- Comentário da coluna
COMMENT ON COLUMN analises.dados_estruturados_json IS 
'Dados estruturados extraídos do PDF pelo Docling em formato JSON';
```

## Próximos Passos

1. ✅ Integração básica do Docling
2. ✅ Extração de informações do aluno
3. ✅ Extração de disciplinas
4. ✅ Armazenamento em JSON
5. 🔄 Melhorar padrões de extração
6. 🔄 Interface para visualizar dados estruturados
7. 🔄 Exportação de dados estruturados
8. 🔄 Análise comparativa de ementas

## Referências

- [Documentação oficial do Docling](https://github.com/DS4SD/docling)
- [Exemplos de uso](https://github.com/DS4SD/docling/tree/main/examples)
- [API Reference](https://ds4sd.github.io/docling/)

## Suporte

Para dúvidas ou problemas:
1. Verifique os logs de erro no Streamlit
2. Consulte este documento
3. Verifique se Docling está instalado corretamente
4. Entre em contato com a equipe de desenvolvimento

