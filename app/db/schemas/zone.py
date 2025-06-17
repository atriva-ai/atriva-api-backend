from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ZoneBase(BaseModel):
    name: str
    camera_id: int
    analytics_id: str
    is_active: bool = True

class ZoneCreate(ZoneBase):
    pass

class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    camera_id: Optional[int] = None
    analytics_id: Optional[str] = None
    is_active: Optional[bool] = None

class ZoneRead(ZoneBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
