from pydantic import BaseModel
from typing import Optional, List, Dict

class CameraBase(BaseModel):
    name: str
    status: bool
    uuid: str
    ip_address: str
    url: Optional[str]
    settings: Optional[dict] = {}
    zone_ids: Optional[List[int]] = []

class CameraCreate(CameraBase):
    analytics_config: Optional[Dict] = {}

class CameraUpdate(CameraBase):
    pass

class CameraOut(CameraBase):
    id: int

    class Config:
        from_attributes = True

class CameraRead(CameraBase):
    id: int
    analytics_config: Optional[Dict] = {}

    class Config:
        from_attributes = True
