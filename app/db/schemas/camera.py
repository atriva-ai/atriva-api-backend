from pydantic import BaseModel, HttpUrl, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict

class CameraBase(BaseModel):
    name: str
    rtsp_url: str
    location: Optional[str] = None
    is_active: bool = True
    zone_ids: Optional[List[int]] = []

class CameraCreate(CameraBase):
    pass

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    rtsp_url: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None
    zone_ids: Optional[List[int]] = None

class CameraInDB(CameraBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Camera(CameraInDB):
    pass

class CameraOut(CameraBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class CameraRead(CameraBase):
    id: int
    analytics_config: Optional[Dict] = {}

    model_config = ConfigDict(from_attributes=True)
