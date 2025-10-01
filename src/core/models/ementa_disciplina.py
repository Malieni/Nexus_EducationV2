from pydantic import BaseModel
from typing import Optional

class Ementa_Disciplina(BaseModel):
    ed_id: int  # INT NOT NULL PRIMARY KEY
    ementa_fk: int  # INT NOT NULL
    disciplina_fk: str  # VARCHAR(15) NOT NULL
    
    class Config:
        from_attributes = True
