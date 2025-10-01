from pydantic import BaseModel
from typing import Optional

class AnaliseCurso(BaseModel):
    """Modelo para a tabela de relacionamento analise_curso"""
    ac_id: Optional[int] = None  # SERIAL PRIMARY KEY
    analise_fk: int  # INTEGER NOT NULL REFERENCES analises(analise_id)
    curso_fk: str  # VARCHAR(50) NOT NULL REFERENCES cursos(codigo_curso)
    
    class Config:
        from_attributes = True
