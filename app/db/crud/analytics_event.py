from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime

from app.db.models.analytics_event import AnalyticsEvent
from app.db.schemas.analytics_event import AnalyticsEventCreate


def create(db: Session, event: AnalyticsEventCreate) -> AnalyticsEvent:
    db_event = AnalyticsEvent(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def bulk_create(db: Session, events: List[AnalyticsEventCreate]) -> None:
    """Insert multiple events in a single commit."""
    if not events:
        return
    db.bulk_insert_mappings(
        AnalyticsEvent,
        [e.model_dump() | {"created_at": datetime.utcnow()} for e in events],
    )
    db.commit()


def get_by_camera(
    db: Session,
    camera_id: int,
    analytics_id: Optional[int] = None,
    event_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 200,
) -> List[AnalyticsEvent]:
    q = db.query(AnalyticsEvent).filter(AnalyticsEvent.camera_id == camera_id)
    if analytics_id is not None:
        q = q.filter(AnalyticsEvent.analytics_id == analytics_id)
    if event_type:
        q = q.filter(AnalyticsEvent.event_type == event_type)
    if start_time:
        q = q.filter(AnalyticsEvent.created_at >= start_time)
    if end_time:
        q = q.filter(AnalyticsEvent.created_at <= end_time)
    return q.order_by(desc(AnalyticsEvent.created_at)).limit(limit).all()


def get_all(
    db: Session,
    camera_id: Optional[int] = None,
    analytics_id: Optional[int] = None,
    event_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 200,
) -> List[AnalyticsEvent]:
    q = db.query(AnalyticsEvent)
    if camera_id is not None:
        q = q.filter(AnalyticsEvent.camera_id == camera_id)
    if analytics_id is not None:
        q = q.filter(AnalyticsEvent.analytics_id == analytics_id)
    if event_type:
        q = q.filter(AnalyticsEvent.event_type == event_type)
    if start_time:
        q = q.filter(AnalyticsEvent.created_at >= start_time)
    if end_time:
        q = q.filter(AnalyticsEvent.created_at <= end_time)
    return q.order_by(desc(AnalyticsEvent.created_at)).limit(limit).all()


def count_by_event_type(
    db: Session,
    camera_id: int,
    analytics_id: int,
    event_type: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> int:
    q = db.query(func.count(AnalyticsEvent.id)).filter(
        AnalyticsEvent.camera_id == camera_id,
        AnalyticsEvent.analytics_id == analytics_id,
        AnalyticsEvent.event_type == event_type,
    )
    if start_time:
        q = q.filter(AnalyticsEvent.created_at >= start_time)
    if end_time:
        q = q.filter(AnalyticsEvent.created_at <= end_time)
    return q.scalar() or 0


def latest_event(
    db: Session, camera_id: int, analytics_id: int
) -> Optional[AnalyticsEvent]:
    return (
        db.query(AnalyticsEvent)
        .filter(
            AnalyticsEvent.camera_id == camera_id,
            AnalyticsEvent.analytics_id == analytics_id,
        )
        .order_by(desc(AnalyticsEvent.created_at))
        .first()
    )
