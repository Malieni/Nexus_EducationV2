from pydantic import BaseModel
from typing import Optional

class Professor_Curso(BaseModel):
    pc_id: int  # INT PRIMARY KEY
    prontuario_professor: str  # VARCHAR(9) NOT NULL
    curso_fk: str  # VARCHAR(50) UNIQUE NOT NULL
    
    class Config:
        from_attributes = True
