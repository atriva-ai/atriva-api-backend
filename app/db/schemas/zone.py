from pydantic import BaseModel
from typing import Optional, Dict

class ZoneBase(BaseModel):
    name: str
    settings: Optional[Dict] = {}
    
class ZoneCreate(ZoneBase):
    camera_id: int  # FK to camera

class ZoneUpdate(ZoneBase):
    pass

'''
class ZoneOut(ZoneBase):
    id: int

    class Config:
        orm_mode = True
'''
        
class ZoneRead(ZoneBase):
    id: int
    camera_id: int

    class Config:
        orm_mode = True
