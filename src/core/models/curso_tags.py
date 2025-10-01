from pydantic import BaseModel
from typing import Optional

class Curso_Tags(BaseModel):
    ct_id: int  # INT NOT NULL PRIMARY KEY
    curso_fk: str  # VARCHAR(50) UNIQUE NOT NULL
    tag_fk: int  # INT NOT NULL
    
    class Config:
        from_attributes = True
