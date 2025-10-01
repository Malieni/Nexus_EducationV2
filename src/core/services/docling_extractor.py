"""
Módulo para extrair dados estruturados de PDFs
Sistema híbrido: PyMuPDF (rápido) + IA (estruturação) + Docling (opcional)
"""
import json
import re
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime
import os

try:
    import fitz  # PyMuPDF para extração rápida
except ImportError:
    print("⚠️ PyMuPDF não está instalado. Execute: pip install pymupdf")


class DoclingExtractor:
    """Extrator híbrido: PyMuPDF (rápido) + IA (estruturação) + Docling (opcional)"""
    
    def __init__(self, use_docling: bool = False):
        """
        Inicializa o extrator
        
        Args:
            use_docling: Se True, usa Docling (lento mas mais preciso).
                        Se False, usa PyMuPDF + IA (rápido e eficiente)
        """
        self.use_docling = use_docling
        self.converter = None
        
        if use_docling:
            try:
                from docling.document_converter import DocumentConverter
                self.converter = DocumentConverter()
                print("🔧 Usando Docling para extração (modo lento)")
            except ImportError:
                print("⚠️ Docling não disponível, usando PyMuPDF + IA")
                self.use_docling = False
        else:
            print("⚡ Usando PyMuPDF + IA para extração rápida")
    
    def extract_from_pdf_fast(self, pdf_path: str) -> Dict:
        """
        Extrai texto de PDF usando PyMuPDF (método rápido)
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            Dict: Dados extraídos (texto + metadados básicos)
        """
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")
            
            text = ""
            metadata = {}
            
            with fitz.open(pdf_path) as pdf:
                # Extrair metadados
                metadata = pdf.metadata
                
                # Extrair texto de todas as páginas
                for page_num in range(len(pdf)):
                    page = pdf[page_num]
                    text += page.get_text()
            
            return {
                "text": text,
                "tables": [],  # PyMuPDF não extrai tabelas automaticamente
                "metadata": metadata,
                "sections": [],
                "extraction_method": "pymupdf_fast"
            }
            
        except Exception as e:
            print(f"Erro ao extrair texto com PyMuPDF: {e}")
            raise
    
    def extract_from_pdf(self, pdf_path: str) -> Dict:
        """
        Extrai dados de PDF usando método apropriado (rápido ou Docling)
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            Dict: Dados extraídos em formato JSON estruturado
        """
        if self.use_docling and self.converter:
            return self._extract_with_docling(pdf_path)
        else:
            return self.extract_from_pdf_fast(pdf_path)
    
    def _extract_with_docling(self, pdf_path: str) -> Dict:
        """Extração usando Docling (método lento mas mais preciso)"""
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")
            
            result = self.converter.convert(pdf_path)
            
            document_data = {
                "text": result.document.export_to_markdown(),
                "tables": [],
                "metadata": {},
                "sections": [],
                "extraction_method": "docling"
            }
            
            if hasattr(result.document, 'tables'):
                for table in result.document.tables:
                    table_data = {
                        "headers": table.get_headers() if hasattr(table, 'get_headers') else [],
                        "rows": table.get_rows() if hasattr(table, 'get_rows') else []
                    }
                    document_data["tables"].append(table_data)
            
            if hasattr(result.document, 'metadata'):
                document_data["metadata"] = result.document.metadata
            
            if hasattr(result.document, 'sections'):
                for section in result.document.sections:
                    section_data = {
                        "title": section.title if hasattr(section, 'title') else "",
                        "content": section.text if hasattr(section, 'text') else ""
                    }
                    document_data["sections"].append(section_data)
            
            return document_data
            
        except Exception as e:
            print(f"Erro ao extrair dados do PDF com Docling: {e}")
            raise
    
    def extract_student_info(self, document_data: Dict) -> Dict:
        """
        Extrai informações específicas do aluno do documento estruturado
        Usa extração adaptativa para diferentes formatos de documento
        
        Args:
            document_data: Dados extraídos pelo Docling
            
        Returns:
            Dict: Informações estruturadas do aluno
        """
        text = document_data.get("text", "")
        
        from .adaptive_extractor import create_adaptive_extractor
        
        adaptive_extractor = create_adaptive_extractor()
        student_info_obj = adaptive_extractor.extract_student_info(text)
        
        student_info = {}
        if student_info_obj.nome:
            student_info["nome"] = student_info_obj.nome
        if student_info_obj.ra:
            student_info["ra"] = student_info_obj.ra
        if student_info_obj.cpf:
            student_info["cpf"] = student_info_obj.cpf
        if student_info_obj.curso:
            student_info["curso"] = student_info_obj.curso
        if student_info_obj.data_matricula:
            student_info["data_matricula"] = student_info_obj.data_matricula
        if student_info_obj.periodo_ingresso:
            student_info["periodo_ingresso"] = student_info_obj.periodo_ingresso
        if student_info_obj.email:
            student_info["email"] = student_info_obj.email
        if student_info_obj.telefone:
            student_info["telefone"] = student_info_obj.telefone
        
        confidence = adaptive_extractor.get_extraction_confidence(text, student_info_obj)
        student_info["extraction_confidence"] = confidence
        
        doc_format = adaptive_extractor.detect_format(text)
        student_info["detected_format"] = doc_format.value
        
        return student_info
    
    def extract_disciplines(self, document_data: Dict) -> list:
        """Extrai disciplinas cursadas do documento"""
        disciplines = []
        
        for table in document_data.get("tables", []):
            headers = table.get("headers", [])
            rows = table.get("rows", [])
            
            col_indices = {
                "codigo": None,
                "nome": None,
                "carga_horaria": None,
                "nota": None,
                "situacao": None
            }
            
            for i, header in enumerate(headers):
                header_lower = str(header).lower()
                if "código" in header_lower or "codigo" in header_lower:
                    col_indices["codigo"] = i
                elif "disciplina" in header_lower or "matéria" in header_lower:
                    col_indices["nome"] = i
                elif "carga" in header_lower or "ch" in header_lower:
                    col_indices["carga_horaria"] = i
                elif "nota" in header_lower or "média" in header_lower:
                    col_indices["nota"] = i
                elif "situação" in header_lower or "status" in header_lower:
                    col_indices["situacao"] = i
            
            for row in rows:
                discipline = {}
                
                if col_indices["codigo"] is not None and len(row) > col_indices["codigo"]:
                    discipline["codigo"] = str(row[col_indices["codigo"]]).strip()
                
                if col_indices["nome"] is not None and len(row) > col_indices["nome"]:
                    discipline["nome"] = str(row[col_indices["nome"]]).strip()
                
                if col_indices["carga_horaria"] is not None and len(row) > col_indices["carga_horaria"]:
                    discipline["carga_horaria"] = str(row[col_indices["carga_horaria"]]).strip()
                
                if col_indices["nota"] is not None and len(row) > col_indices["nota"]:
                    discipline["nota"] = str(row[col_indices["nota"]]).strip()
                
                if col_indices["situacao"] is not None and len(row) > col_indices["situacao"]:
                    discipline["situacao"] = str(row[col_indices["situacao"]]).strip()
                
                if discipline:
                    disciplines.append(discipline)
        
        return disciplines
    
    def process_pdf_to_json(self, pdf_path: str, ai_client=None) -> Dict:
        """
        Processa PDF completo e retorna dados estruturados em JSON
        Sistema híbrido: extração rápida + IA para estruturação
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            ai_client: Cliente de IA para estruturar dados (opcional)
            
        Returns:
            Dict: Dados estruturados completos do documento
        """
        try:
            document_data = self.extract_from_pdf(pdf_path)
            
            if ai_client and not self.use_docling:
                structured_data = self._structure_with_ai(document_data, ai_client)
            else:
                student_info = self.extract_student_info(document_data)
                disciplines = self.extract_disciplines(document_data)
                
                structured_data = {
                    "student_info": student_info,
                    "disciplines": disciplines,
                    "raw_text": document_data.get("text", ""),
                    "tables": document_data.get("tables", []),
                    "metadata": document_data.get("metadata", {}),
                    "sections": document_data.get("sections", []),
                    "extraction_info": {
                        "method": "docling_adaptive",
                        "confidence": student_info.get("extraction_confidence", 0.0),
                        "detected_format": student_info.get("detected_format", "unknown"),
                        "timestamp": datetime.now().isoformat()
                    }
                }
            
            self._record_extraction_for_learning(structured_data, pdf_path)
            
            return structured_data
            
        except Exception as e:
            print(f"Erro ao processar PDF para JSON: {e}")
            raise
    
    def _structure_with_ai(self, document_data: Dict, ai_client) -> Dict:
        """Usa IA para estruturar dados extraídos rapidamente"""
        try:
            text = document_data.get("text", "")
            
            structure_prompt = f"""
            Analise este histórico escolar e extraia as informações do aluno em formato JSON estruturado.

            Texto do histórico:
            {text[:3000]}

            Retorne APENAS um JSON válido com esta estrutura:
            {{
                "student_info": {{
                    "nome": "Nome completo do aluno",
                    "ra": "RA/Prontuário",
                    "cpf": "CPF se disponível",
                    "curso": "Nome do curso",
                    "data_matricula": "Data de matrícula",
                    "periodo_ingresso": "Período de ingresso"
                }},
                "disciplines": [],
                "extraction_confidence": 0.85
            }}

            Se alguma informação não estiver disponível, use null.
            """
            
            ai_response = ai_client.generate_response(structure_prompt)
            
            try:
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    structured_json = json.loads(json_match.group(0))
                    
                    return {
                        "student_info": structured_json.get("student_info", {}),
                        "disciplines": structured_json.get("disciplines", []),
                        "raw_text": text,
                        "tables": document_data.get("tables", []),
                        "metadata": document_data.get("metadata", {}),
                        "sections": document_data.get("sections", []),
                        "extraction_info": {
                            "method": "pymupdf_ai_structured",
                            "confidence": structured_json.get("extraction_confidence", 0.8),
                            "detected_format": "ai_structured",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                else:
                    raise ValueError("JSON não encontrado na resposta da IA")
                    
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Erro ao parsear JSON da IA: {e}")
                return self._fallback_extraction(document_data)
                
        except Exception as e:
            print(f"Erro ao estruturar com IA: {e}")
            return self._fallback_extraction(document_data)
    
    def _fallback_extraction(self, document_data: Dict) -> Dict:
        """Extração tradicional como fallback"""
        student_info = self.extract_student_info(document_data)
        disciplines = self.extract_disciplines(document_data)
        
        return {
            "student_info": student_info,
            "disciplines": disciplines,
            "raw_text": document_data.get("text", ""),
            "tables": document_data.get("tables", []),
            "metadata": document_data.get("metadata", {}),
            "sections": document_data.get("sections", []),
            "extraction_info": {
                "method": "fallback_traditional",
                "confidence": student_info.get("extraction_confidence", 0.5),
                "detected_format": student_info.get("detected_format", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def _record_extraction_for_learning(self, structured_data: Dict, pdf_path: str):
        """Registra extração para sistema de aprendizado"""
        try:
            from .format_learning import create_learning_system, ExtractionResult
            
            learning_system = create_learning_system()
            
            student_info = structured_data.get("student_info", {})
            extraction_info = structured_data.get("extraction_info", {})
            
            success = (
                bool(student_info.get("nome")) and 
                extraction_info.get("confidence", 0) > 0.5
            )
            
            result = ExtractionResult(
                document_type=extraction_info.get("detected_format", "unknown"),
                extracted_fields=student_info,
                confidence=extraction_info.get("confidence", 0.0),
                extraction_method=extraction_info.get("method", "docling"),
                timestamp=extraction_info.get("timestamp", datetime.now().isoformat()),
                success=success
            )
            
            learning_system.record_extraction(result)
            
        except Exception as e:
            print(f"Erro ao registrar extração para aprendizado: {e}")
    
    def save_to_json_file(self, data: Dict, output_path: str):
        """Salva dados estruturados em arquivo JSON"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar JSON: {e}")
            raise


def extract_pdf_with_docling(pdf_path: str) -> Dict:
    """
    Função helper para extrair dados de PDF usando Docling
    
    Args:
        pdf_path: Caminho para o arquivo PDF
        
    Returns:
        Dict: Dados estruturados do PDF
    """
    extractor = DoclingExtractor()
    return extractor.process_pdf_to_json(pdf_path)
