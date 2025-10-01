from pydantic import BaseModel
from typing import Optional

class Analise(BaseModel):
    analise_id: Optional[int] = None  # INT AUTO_INCREMENT NOT NULL PRIMARY KEY
    nome_aluno: str # VARCHAR (255) NOT NULL 
    ementa_fk: int  # INT NOT NULL
    adequado: bool  # BOOLEAN NOT NULL
    score: int # INT not null
    texto_analise: str  # VARCHAR(255) NOT NULL
    materias_restantes: Optional[str] = None  # VARCHAR(255)
    dados_estruturados_json: Optional[str] = None  # TEXT - Dados estruturados extraídos pelo Docling em JSON
    
    class Config:
        from_attributes = True
