from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.db.crud import analytics_event as crud
from app.db.models.analytics import Analytics
from app.db.models.camera import Camera
from app.db.schemas.analytics_event import AnalyticsEvent, AnalyticsEventSummary

router = APIRouter(prefix="/api/v1/analytics-events", tags=["analytics-events"])

# The processor instance is injected by main.py after startup.
# Routes that need live state access it via this module-level reference.
processor = None  # set by main.py: analytics_events.processor = _processor


@router.get("/", response_model=List[AnalyticsEvent])
def list_events(
    camera_id: Optional[int] = Query(None),
    analytics_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(200, le=1000),
    db: Session = Depends(get_db),
):
    return crud.get_all(
        db,
        camera_id=camera_id,
        analytics_id=analytics_id,
        event_type=event_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )


@router.get("/live", response_model=List[Dict[str, Any]])
def live_state():
    """
    Real-time snapshot of all active analytics states from the processor.
    Returns line counts and zone occupancy without hitting the DB.
    """
    if processor is None:
        return []
    return processor.live_summary()


@router.get("/summary", response_model=List[AnalyticsEventSummary])
def summary(
    camera_id: Optional[int] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Aggregate analytics results per (camera, analytics) pair.
    Useful for dashboard charts and the person-activity page.
    """
    q = db.query(Analytics)
    if camera_id is not None:
        q = q.join(Analytics.cameras).filter(Camera.id == camera_id)
    all_analytics = q.filter(Analytics.is_active == True).all()

    result: List[AnalyticsEventSummary] = []
    for anal in all_analytics:
        cam_ids = [c.id for c in anal.cameras]
        if camera_id is not None:
            cam_ids = [c for c in cam_ids if c == camera_id]
        for cid in cam_ids:
            total_in = crud.count_by_event_type(
                db, cid, anal.id, "line_cross_in", start_time, end_time
            )
            total_out = crud.count_by_event_type(
                db, cid, anal.id, "line_cross_out", start_time, end_time
            )
            zone_entries = crud.count_by_event_type(
                db, cid, anal.id, "zone_enter", start_time, end_time
            )
            latest = crud.latest_event(db, cid, anal.id)

            # Current live zone count from in-memory processor state
            live_zone = (
                processor.current_zone_count(cid, anal.id) if processor else 0
            )

            result.append(AnalyticsEventSummary(
                camera_id=cid,
                analytics_id=anal.id,
                analytics_type=anal.type,
                total_in=total_in,
                total_out=total_out,
                current_zone_count=live_zone,
                event_count=total_in + total_out + zone_entries,
                last_event_at=latest.created_at if latest else None,
            ))

    return result


@router.get("/camera/{camera_id}", response_model=List[AnalyticsEvent])
def events_for_camera(
    camera_id: int,
    analytics_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    return crud.get_by_camera(
        db,
        camera_id=camera_id,
        analytics_id=analytics_id,
        event_type=event_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )


@router.get("/camera/{camera_id}/line-counts")
def live_line_counts(camera_id: int, analytics_id: int, db: Session = Depends(get_db)):
    """
    Current cumulative IN/OUT line-crossing counts from the processor.
    Falls back to DB totals when processor is not available.
    """
    if processor is not None:
        return processor.current_line_counts(camera_id, analytics_id)
    return {
        "in": crud.count_by_event_type(db, camera_id, analytics_id, "line_cross_in"),
        "out": crud.count_by_event_type(db, camera_id, analytics_id, "line_cross_out"),
    }
