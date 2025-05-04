from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

# Association table for many-to-many relationship between Camera and Zone
camera_zones = Table(
    "camera_zones",
    Base.metadata,
    Column("camera_id", Integer, ForeignKey("cameras.id"), primary_key=True),
    Column("zone_id", Integer, ForeignKey("zones.id"), primary_key=True),
)

class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

    # Back reference to cameras in this zone
    cameras = relationship("Camera", secondary=camera_zones, back_populates="zones")
