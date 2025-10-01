from pydantic import BaseModel
from typing import Optional

class Cursos_Disciplina(BaseModel):
    cd_id: int  # INT NOT NULL PRIMARY KEY
    curso_fk: str  # VARCHAR(50) UNIQUE NOT NULL
    disciplina_fk: str  # VARCHAR(15) NOT NULL
    
    class Config:
        from_attributes = True
