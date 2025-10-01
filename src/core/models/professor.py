from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Professor(BaseModel):
    prontuario: str  # VARCHAR(9) PRIMARY KEY
    nome: str  # VARCHAR(150) NOT NULL
    email_educacional: str  # VARCHAR(150) UNIQUE NOT NULL
    senha: str  # VARCHAR(50) NOT NULL
    
    class Config:
        from_attributes = True