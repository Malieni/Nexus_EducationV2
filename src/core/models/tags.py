from pydantic import BaseModel
from typing import Optional

class Tags(BaseModel):
    id_tag: Optional[int] = None  # INT AUTO_INCREMENT PRIMARY KEY
    nome: str  # VARCHAR(150)
    
    class Config:
        from_attributes = True
