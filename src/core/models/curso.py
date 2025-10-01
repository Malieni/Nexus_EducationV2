from pydantic import BaseModel
from typing import Optional

class Cursos(BaseModel):
    codigo_curso: str  # VARCHAR(50) UNIQUE PRIMARY KEY
    nome: str  # VARCHAR(150) NOT NULL
    descricao_curso: str # VARCHAR(MAX) NOT NULL
    
    class Config:
        from_attributes = True
