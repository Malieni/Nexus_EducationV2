from pydantic import BaseModel
from typing import Optional

class Disciplinas(BaseModel):
    id_disciplina: str  # VARCHAR(15) PRIMARY KEY
    nome: str  # VARCHAR(150) NOT NULL
    carga_horaria: Optional[int] = None  # INT
    
    class Config:
        from_attributes = True
