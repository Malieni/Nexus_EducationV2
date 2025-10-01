"""
Extrator adaptativo que se ajusta automaticamente a diferentes formatos de documento
"""
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class DocumentFormat(Enum):
    """Formatos de documento suportados"""
    IFSP_HISTORICO = "ifsp_historico"
    IFSP_EMENTA = "ifsp_ementa"
    GENERIC_HISTORICO = "generic_historico"
    UNKNOWN = "unknown"

@dataclass
class StudentInfo:
    """Estrutura para informações do aluno"""
    nome: Optional[str] = None
    ra: Optional[str] = None
    cpf: Optional[str] = None
    curso: Optional[str] = None
    data_matricula: Optional[str] = None
    periodo_ingresso: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None

class AdaptiveExtractor:
    """Extrator que se adapta automaticamente ao formato do documento"""
    
    def __init__(self):
        self.detection_patterns = {
            DocumentFormat.IFSP_HISTORICO: [
                r"INSTITUTO FEDERAL DE EDUCAÇÃO, CIÊNCIA E TECNOLOGIA DE SÃO PAULO",
                r"## HISTÓRICO ESCOLAR",
                r"BP\d+[A-Z]?",  # Padrão RA do IFSP
            ],
            DocumentFormat.IFSP_EMENTA: [
                r"INSTITUTO FEDERAL.*SÃO PAULO",
                r"EMENTA",
                r"COMPONENTES CURRICULARES",
            ],
            DocumentFormat.GENERIC_HISTORICO: [
                r"HISTÓRICO.*ESCOLAR",
                r"NOTAS.*ESCOLARES",
                r"BOLETIM.*ESCOLAR",
            ]
        }
        
        self.extraction_rules = {
            DocumentFormat.IFSP_HISTORICO: self._extract_ifsp_historico,
            DocumentFormat.IFSP_EMENTA: self._extract_ifsp_ementa,
            DocumentFormat.GENERIC_HISTORICO: self._extract_generic_historico,
        }
    
    def detect_format(self, text: str) -> DocumentFormat:
        """Detecta automaticamente o formato do documento"""
        text_lower = text.lower()
        
        # Contar matches para cada formato
        format_scores = {}
        
        for format_type, patterns in self.detection_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 1
            
            # Normalizar pelo número de padrões
            format_scores[format_type] = score / len(patterns)
        
        # Retornar formato com maior score
        best_format = max(format_scores.items(), key=lambda x: x[1])
        
        if best_format[1] > 0.3:  # Threshold mínimo
            return best_format[0]
        else:
            return DocumentFormat.UNKNOWN
    
    def extract_student_info(self, text: str) -> StudentInfo:
        """Extrai informações do aluno adaptando-se ao formato detectado"""
        # Detectar formato
        doc_format = self.detect_format(text)
        
        print(f"🔍 Formato detectado: {doc_format.value}")
        
        # Extrair usando regras específicas
        if doc_format in self.extraction_rules:
            return self.extraction_rules[doc_format](text)
        else:
            # Fallback para extração genérica
            return self._extract_generic(text)
    
    def _extract_ifsp_historico(self, text: str) -> StudentInfo:
        """Extração específica para histórico do IFSP"""
        info = StudentInfo()
        
        # Nome - na seção COMPONENTES CURRICULARES
        nome_pattern = r"##\s+COMPONENTES\s+CURRICULARES.*?Nome:\s*\n\s*([^\n]+)"
        match = re.search(nome_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            nome = match.group(1).strip()
            if not any(x in nome for x in ['MINISTÉRIO', 'INSTITUTO', 'FEDERAL']):
                info.nome = nome
        
        # RA/Prontuário
        ra_pattern = r"([A-Z]{2}\d{6,}[A-Z]?)"
        match = re.search(ra_pattern, text)
        if match:
            info.ra = match.group(1).strip()
        
        # CPF
        cpf_pattern = r"CPF:\s*(\d{3}\.\d{3}\.\d{3}-\d{2})"
        match = re.search(cpf_pattern, text)
        if match:
            info.cpf = match.group(1).strip()
        
        # Curso
        curso_pattern = r"Curso:\s*\n\s*([^\n]+)"
        match = re.search(curso_pattern, text, re.IGNORECASE)
        if match:
            curso = match.group(1).strip()
            if len(curso) > 5:
                info.curso = curso
        
        # Data de matrícula
        matricula_pattern = r"Data de Matrícula:\s*(\d{2}/\d{2}/\d{4})"
        match = re.search(matricula_pattern, text)
        if match:
            info.data_matricula = match.group(1).strip()
        
        # Período de ingresso
        periodo_pattern = r"Ano/Período de Ingresso:\s*(\d{4}/\d)"
        match = re.search(periodo_pattern, text)
        if match:
            info.periodo_ingresso = match.group(1).strip()
        
        return info
    
    def _extract_ifsp_ementa(self, text: str) -> StudentInfo:
        """Extração específica para ementa do IFSP"""
        info = StudentInfo()
        
        # Para ementas, informações são mais limitadas
        # Nome do curso
        curso_pattern = r"Curso:\s*([^\n]+)"
        match = re.search(curso_pattern, text, re.IGNORECASE)
        if match:
            info.curso = match.group(1).strip()
        
        return info
    
    def _extract_generic_historico(self, text: str) -> StudentInfo:
        """Extração genérica para históricos escolares"""
        info = StudentInfo()
        
        # Padrões genéricos mais flexíveis
        nome_patterns = [
            r"Nome\s*(?:Completo)?[:\s]+([^\n]+)",
            r"Aluno[:\s]+([^\n]+)",
            r"Estudante[:\s]+([^\n]+)",
        ]
        
        for pattern in nome_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                nome = match.group(1).strip()
                if len(nome) > 3 and len(nome) < 100:
                    info.nome = nome
                    break
        
        # RA/Matrícula genérico
        ra_patterns = [
            r"(?:RA|Matrícula|Registro)[:\s]+(\d+[A-Z]?)",
            r"(\d{6,}[A-Z]?)",
        ]
        
        for pattern in ra_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info.ra = match.group(1).strip()
                break
        
        # Curso genérico
        curso_patterns = [
            r"Curso[:\s]+([^\n]+)",
            r"Graduação[:\s]+([^\n]+)",
        ]
        
        for pattern in curso_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                curso = match.group(1).strip()
                if len(curso) > 5:
                    info.curso = curso
                    break
        
        return info
    
    def _extract_generic(self, text: str) -> StudentInfo:
        """Extração completamente genérica como último recurso"""
        info = StudentInfo()
        
        # Buscar qualquer linha que pareça um nome
        lines = text.split('\n')
        for line in lines[:50]:  # Primeiras 50 linhas
            line_clean = line.strip()
            if (len(line_clean) > 5 and len(line_clean) < 80 and
                not any(x in line_clean for x in ['##', 'http', '@', '.com', 'MINISTÉRIO', 'INSTITUTO']) and
                re.search(r'^[A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ][a-záàâãéèêíïóôõöúçñ]+(\s+[A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ][a-záàâãéèêíïóôõöúçñ]+)+$', line_clean)):
                info.nome = line_clean
                break
        
        return info
    
    def get_extraction_confidence(self, text: str, extracted_info: StudentInfo) -> float:
        """Calcula a confiança da extração (0.0 a 1.0)"""
        confidence = 0.0
        
        # Nome extraído corretamente
        if extracted_info.nome and len(extracted_info.nome) > 3:
            confidence += 0.3
        
        # RA/Prontuário encontrado
        if extracted_info.ra:
            confidence += 0.2
        
        # CPF encontrado
        if extracted_info.cpf:
            confidence += 0.2
        
        # Curso encontrado
        if extracted_info.curso:
            confidence += 0.2
        
        # Informações adicionais
        if extracted_info.data_matricula or extracted_info.periodo_ingresso:
            confidence += 0.1
        
        return min(confidence, 1.0)

def create_adaptive_extractor():
    """Factory function para criar extrator adaptativo"""
    return AdaptiveExtractor()
