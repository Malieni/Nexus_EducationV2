import re, uuid, os
import fitz
import json
from datetime import datetime
from core.models.analise import Analise
from core.models.ementa import Ementa
from core.models.disciplinas import Disciplinas
from core.database.database_separado import AnalyseDatabaseSeparado

# Importar extrator Docling
try:
    from src.core.services.docling_extractor import DoclingExtractor, extract_pdf_with_docling
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    print("⚠️ Docling não disponível. Usando extração padrão.")

def convert_datetime_for_json(data: dict) -> dict:
    """Converte objetos datetime em strings para serialização JSON"""
    converted = data.copy()
    for key, value in converted.items():
        if isinstance(value, datetime):
            converted[key] = value.isoformat()
        elif isinstance(value, dict):
            converted[key] = convert_datetime_for_json(value)
    return converted

def read_pdf(file_path):
    """Extrai texto de PDF usando PyMuPDF (método tradicional)"""
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text


def read_pdf_with_docling(file_path: str, ai_client=None) -> dict:
    """
    Extrai dados estruturados de PDF usando sistema híbrido (rápido + IA)
    
    Args:
        file_path: Caminho para o arquivo PDF
        ai_client: Cliente de IA para estruturar dados (opcional)
        
    Returns:
        dict: Dados estruturados incluindo texto, tabelas e metadados
    """
    try:
        # Usar extrator híbrido (rápido por padrão)
        extractor = DoclingExtractor(use_docling=False)  # Modo rápido
        structured_data = extractor.process_pdf_to_json(file_path, ai_client)
        
        return {
            "text": structured_data.get("raw_text", ""),
            "structured_data": structured_data,
            "method": structured_data.get("extraction_info", {}).get("method", "pymupdf_fast")
        }
    except Exception as e:
        print(f"Erro no sistema híbrido: {e}. Fallback para PyMuPDF simples.")
        return {
            "text": read_pdf(file_path),
            "structured_data": None,
            "method": "pymupdf_fallback"
        }


def extract_data_analysis(resumo_ementa: str, ementa_fk: int, prontuario_professor: str, score: float, texto_analise: str) -> Analise:
    """
    Extrai dados de análise do resumo da ementa e cria um objeto Analise
    
    Args:
        resumo_ementa: Texto do resumo da ementa em markdown
        ementa_fk: ID da ementa no banco de dados
        prontuario_professor: Prontuário do professor que fez a análise
        score: Pontuação da análise (0-10)
        texto_analise: Texto completo da análise
        
    Returns:
        Analise: Objeto de análise pronto para salvar no banco
    """
    patterns = {
        "nome_aluno": r"(?:## Nome Completo\s*|Nome Completo\s*\|\s*Valor\s*\|\s*\S*\s*\|\s*)(.*)",
        "disciplinas": r"## Disciplinas\s*([\s\S]*?)(?=##|$)",
        "habilidades": r"## Habilidades\s*([\s\S]*?)(?=##|$)"
    }

    def clean_string(string: str) -> str:
        return re.sub(r"[\*\-]+", "", string).strip()

    # Extrair nome do aluno
    nome_aluno = "Nome não identificado"
    nome_match = re.search(patterns["nome_aluno"], resumo_ementa)
    if nome_match:
        nome_aluno = clean_string(nome_match.group(1))

    # Extrair disciplinas
    disciplinas_text = ""
    disciplinas_match = re.search(patterns["disciplinas"], resumo_ementa)
    if disciplinas_match:
        disciplinas_text = clean_string(disciplinas_match.group(1))

    # Determinar se é adequado baseado no score
    adequado = score >= 7.0

    # Criar objeto Analise
    analise = Analise(
        analise_id=None,  # Será definido pelo banco
        nome_aluno=nome_aluno,
        ementa_fk=ementa_fk,
        adequado=adequado,
        score=int(score * 10),  # Converter para escala 0-100
        texto_analise=texto_analise,
        materias_restantes=disciplinas_text if not adequado else None
    )

    return analise

def get_pdf_paths(directory):
    """
    Busca todos os arquivos PDF em um diretório
    
    Args:
        directory: Caminho do diretório para buscar PDFs
        
    Returns:
        List[str]: Lista de caminhos dos arquivos PDF encontrados
    """
    pdf_files = []

    for filename in os.listdir(directory):
        if filename.endswith('.pdf'):
            file_path = os.path.join(directory, filename)
            pdf_files.append(file_path)

    return pdf_files


def process_pdf_and_save_ementa(pdf_path: str, drive_id: str = None) -> int:
    """
    Processa um PDF e salva como ementa no banco de dados
    
    Args:
        pdf_path: Caminho para o arquivo PDF
        drive_id: ID do arquivo no Google Drive (opcional)
        
    Returns:
        int: ID da ementa salva no banco
    """
    try:
        # Extrair texto do PDF
        texto_ementa = read_pdf(pdf_path)
        
        if not texto_ementa.strip():
            raise ValueError("PDF não contém texto extraível")
        
        # Criar objeto Ementa
        ementa = Ementa(
            id_ementa=None,  # Será definido pelo banco
            drive_id=drive_id,
            data_upload=datetime.now()
        )
        
        # Conectar ao banco de dados
        database = AnalyseDatabaseSeparado()
        
        # Salvar ementa no banco
        ementa_dict = ementa.model_dump()
        ementa_dict.pop('id_ementa', None)  # Remover ID para auto-incremento
        
        # Converter datetime para string para serialização JSON
        ementa_dict = convert_datetime_for_json(ementa_dict)
        
        ementa_id = database.ementa.insert(ementa_dict)
        
        return ementa_id
        
    except Exception as e:
        print(f"Erro ao processar PDF {pdf_path}: {e}")
        raise


def process_pdf_and_create_analysis(pdf_path: str, prontuario_professor: str, 
                                  curso_codigo: str, ai_client) -> dict:
    """
    Processa um PDF completo: extrai texto, gera resumo, análise e salva no banco
    
    Args:
        pdf_path: Caminho para o arquivo PDF
        prontuario_professor: Prontuário do professor que está analisando
        curso_codigo: Código do curso para análise
        ai_client: Cliente de IA para gerar resumo e análise
        
    Returns:
        dict: Resultado do processamento com IDs e dados salvos
    """
    try:
        # 1. Extrair texto do PDF
        texto_ementa = read_pdf(pdf_path)
        
        if not texto_ementa.strip():
            raise ValueError("PDF não contém texto extraível")
        
        # 2. Salvar ementa no banco
        ementa_id = process_pdf_and_save_ementa(pdf_path)
        
        # 3. Gerar resumo da ementa usando IA
        resumo_ementa = ai_client.resume_ementa(texto_ementa)
        
        # 4. Buscar dados do curso para análise
        database = AnalyseDatabaseSeparado()
        curso_data = database.get_curso_by_codigo(curso_codigo)
        
        if not curso_data:
            raise ValueError(f"Curso {curso_codigo} não encontrado")
        
        # 5. Gerar score da análise
        score = ai_client.generate_score(resumo_ementa, curso_data)
        
        if score is None:
            score = 5.0  # Score padrão se não conseguir gerar
        
        # 6. Gerar texto de análise detalhada
        texto_analise = ai_client.generate_opinion(resumo_ementa, curso_data)
        
        # 7. Criar objeto de análise
        analise = extract_data_analysis(
            resumo_ementa=resumo_ementa,
            ementa_fk=ementa_id,
            prontuario_professor=prontuario_professor,
            score=score,
            texto_analise=texto_analise
        )
        
        # 8. Salvar análise no banco
        analise_dict = analise.model_dump()
        analise_dict.pop('analise_id', None)  # Remover ID para auto-incremento
        analise_dict['professor_id'] = prontuario_professor  # Usar professor_id para Supabase
        
        # Converter datetime para string para serialização JSON
        analise_dict = convert_datetime_for_json(analise_dict)
        
        # Salvar análise com relacionamento ao curso
        analise_result = database.create_analise(analise_dict, curso_codigo=curso_codigo)
        
        if analise_result:
            analise_id = analise_result.get('analise_id')
        else:
            raise ValueError("Falha ao salvar análise no banco de dados")
        
        return {
            "success": True,
            "ementa_id": ementa_id,
            "analise_id": analise_id,
            "score": score,
            "nome_aluno": analise.nome_aluno,
            "adequado": analise.adequado,
            "resumo_ementa": resumo_ementa,
            "texto_analise": texto_analise
        }
        
    except Exception as e:
        print(f"Erro ao processar PDF completo {pdf_path}: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def batch_process_pdfs(pdf_directory: str, prontuario_professor: str, 
                      curso_codigo: str, ai_client) -> list:
    """
    Processa múltiplos PDFs em lote
    
    Args:
        pdf_directory: Diretório contendo os PDFs
        prontuario_professor: Prontuário do professor
        curso_codigo: Código do curso para análise
        ai_client: Cliente de IA
        
    Returns:
        list: Lista de resultados do processamento
    """
    pdf_files = get_pdf_paths(pdf_directory)
    results = []
    
    for pdf_path in pdf_files:
        print(f"Processando: {pdf_path}")
        result = process_pdf_and_create_analysis(
            pdf_path, prontuario_professor, curso_codigo, ai_client
        )
        results.append({
            "pdf_path": pdf_path,
            "result": result
        })
    
    return results