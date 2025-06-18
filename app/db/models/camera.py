from sqlalchemy import Column, Integer, String, Boolean, DateTime, Table, ForeignKey
from datetime import datetime
from app.database import Base
from sqlalchemy.orm import relationship

# Association table for many-to-many relationship between Camera and Analytics
camera_analytics = Table(
    'camera_analytics',
    Base.metadata,
    Column('camera_id', Integer, ForeignKey('cameras.id'), primary_key=True),
    Column('analytics_id', Integer, ForeignKey('analytics.id'), primary_key=True)
)

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    rtsp_url = Column(String, nullable=False)
    location = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    zones = relationship("Zone", back_populates="camera")
    analytics = relationship("Analytics", secondary=camera_analytics, back_populates="cameras")

    def __repr__(self):
        return f"<Camera(id={self.id}, name='{self.name}', rtsp_url='{self.rtsp_url}')>"
