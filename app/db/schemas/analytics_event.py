from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime


class AnalyticsEventBase(BaseModel):
    camera_id: int
    analytics_id: int
    event_type: str
    value: Optional[Dict[str, Any]] = None


class AnalyticsEventCreate(AnalyticsEventBase):
    pass


class AnalyticsEvent(AnalyticsEventBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyticsEventSummary(BaseModel):
    camera_id: int
    analytics_id: int
    analytics_type: str
    total_in: int = 0
    total_out: int = 0
    current_zone_count: int = 0
    avg_dwell_s: Optional[float] = None
    event_count: int = 0
    last_event_at: Optional[datetime] = None
