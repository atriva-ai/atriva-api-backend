from sqlalchemy import Column, String, Boolean, Integer, JSON, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
from .zone import camera_zones
import uuid

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)  # Internal DB ID
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)  # App-facing UUID

    name = Column(String, nullable=False)
    status = Column(Boolean, default=True)  # True = enabled

    ip_address = Column(String, nullable=True)
    stream_url = Column(String, nullable=True)

    settings = Column(JSON, nullable=True)  # Codec, resolution, frame rate, etc.

    # Optional: many-to-many relationship with zones
    # Use an association table for flexible mapping
    zones = relationship("Zone", secondary="camera_zones", back_populates="cameras")
