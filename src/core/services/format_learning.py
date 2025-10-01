"""
Sistema de aprendizado contínuo para novos formatos de documento
"""
import json
import os
from typing import Dict, List, Any
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class ExtractionResult:
    """Resultado de uma extração"""
    document_type: str
    extracted_fields: Dict[str, Any]
    confidence: float
    extraction_method: str
    timestamp: str
    success: bool

class FormatLearningSystem:
    """Sistema que aprende novos formatos de documento"""
    
    def __init__(self, learning_file: str = "src/data/format_learning.json"):
        self.learning_file = learning_file
        self.extraction_history = []
        self.load_learning_data()
    
    def load_learning_data(self):
        """Carrega dados de aprendizado anteriores"""
        if os.path.exists(self.learning_file):
            try:
                with open(self.learning_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.extraction_history = data.get('extraction_history', [])
            except Exception as e:
                print(f"Erro ao carregar dados de aprendizado: {e}")
                self.extraction_history = []
    
    def save_learning_data(self):
        """Salva dados de aprendizado"""
        os.makedirs(os.path.dirname(self.learning_file), exist_ok=True)
        
        try:
            with open(self.learning_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'extraction_history': self.extraction_history,
                    'last_updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar dados de aprendizado: {e}")
    
    def record_extraction(self, result: ExtractionResult):
        """Registra resultado de extração para aprendizado"""
        self.extraction_history.append(asdict(result))
        
        # Manter apenas os últimos 100 registros
        if len(self.extraction_history) > 100:
            self.extraction_history = self.extraction_history[-100:]
        
        self.save_learning_data()
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de aprendizado"""
        if not self.extraction_history:
            return {"message": "Nenhum dado de aprendizado disponível"}
        
        total_extractions = len(self.extraction_history)
        successful_extractions = sum(1 for r in self.extraction_history if r['success'])
        avg_confidence = sum(r['confidence'] for r in self.extraction_history) / total_extractions
        
        # Contar por tipo de documento
        document_types = {}
        for result in self.extraction_history:
            doc_type = result['document_type']
            if doc_type not in document_types:
                document_types[doc_type] = 0
            document_types[doc_type] += 1
        
        # Contar por método de extração
        extraction_methods = {}
        for result in self.extraction_history:
            method = result['extraction_method']
            if method not in extraction_methods:
                extraction_methods[method] = 0
            extraction_methods[method] += 1
        
        return {
            "total_extractions": total_extractions,
            "successful_extractions": successful_extractions,
            "success_rate": f"{(successful_extractions/total_extractions)*100:.1f}%",
            "average_confidence": f"{avg_confidence:.2f}",
            "document_types": document_types,
            "extraction_methods": extraction_methods,
            "last_extraction": self.extraction_history[-1]['timestamp'] if self.extraction_history else None
        }
    
    def suggest_improvements(self) -> List[str]:
        """Sugere melhorias baseadas no histórico"""
        suggestions = []
        
        if not self.extraction_history:
            return ["Nenhum dado disponível para sugestões"]
        
        # Analisar taxa de sucesso por tipo
        document_types = {}
        for result in self.extraction_history:
            doc_type = result['document_type']
            if doc_type not in document_types:
                document_types[doc_type] = {'total': 0, 'success': 0}
            document_types[doc_type]['total'] += 1
            if result['success']:
                document_types[doc_type]['success'] += 1
        
        for doc_type, stats in document_types.items():
            success_rate = stats['success'] / stats['total']
            if success_rate < 0.7:
                suggestions.append(f"Tipo '{doc_type}' tem baixa taxa de sucesso ({success_rate*100:.1f}%). Considere ajustar padrões de extração.")
        
        # Analisar confiança média
        avg_confidence = sum(r['confidence'] for r in self.extraction_history) / len(self.extraction_history)
        if avg_confidence < 0.6:
            suggestions.append("Confiança média baixa. Considere melhorar validação de dados extraídos.")
        
        # Analisar métodos de extração
        methods = {}
        for result in self.extraction_history:
            method = result['extraction_method']
            if method not in methods:
                methods[method] = {'total': 0, 'success': 0}
            methods[method]['total'] += 1
            if result['success']:
                methods[method]['success'] += 1
        
        for method, stats in methods.items():
            success_rate = stats['success'] / stats['total']
            if success_rate < 0.5:
                suggestions.append(f"Método '{method}' tem baixo desempenho ({success_rate*100:.1f}%). Considere revisar implementação.")
        
        if not suggestions:
            suggestions.append("Sistema funcionando bem! Nenhuma melhoria crítica necessária.")
        
        return suggestions

def create_learning_system() -> FormatLearningSystem:
    """Factory function para criar sistema de aprendizado"""
    return FormatLearningSystem()
