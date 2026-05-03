from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Index
from datetime import datetime
from app.database import Base


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    analytics_id = Column(Integer, ForeignKey("analytics.id"), nullable=False)
    # event_type values: line_cross_in, line_cross_out, zone_enter, zone_exit,
    #                    zone_count_snapshot, dwell_alert, people_count_snapshot
    event_type = Column(String, nullable=False)
    # event-specific payload, e.g.:
    #   line_cross_*:      {"track_id": 3, "count_in": 5, "count_out": 2}
    #   zone_count_*:      {"track_id": 3, "zone_count": 4}
    #   dwell_alert:       {"track_id": 3, "dwell_s": 47.2}
    #   people_count_*:    {"count": 7}
    value = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_analytics_events_camera_created", "camera_id", "created_at"),
        Index("ix_analytics_events_analytics_created", "analytics_id", "created_at"),
    )

    def __repr__(self):
        return (
            f"<AnalyticsEvent(id={self.id}, camera_id={self.camera_id}, "
            f"analytics_id={self.analytics_id}, event_type='{self.event_type}')>"
        )
