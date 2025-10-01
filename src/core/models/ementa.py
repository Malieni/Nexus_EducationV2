from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Ementa(BaseModel):
    id_ementa: Optional[int] = None  # INT AUTO_INCREMENT PRIMARY KEY (gerado pelo Supabase)
    drive_id: Optional[str] = None  # VARCHAR(255)
    data_upload: datetime  # DATETIME NOT NULL DEFAULT GETDATE()
    
    class Config:
        from_attributes = True

class EmentaCreate(BaseModel):
    """Modelo para criação de ementa (sem id_ementa)"""
    drive_id: Optional[str] = None
    data_upload: datetime
    
    class Config:
        from_attributes = True
