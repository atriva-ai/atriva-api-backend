from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.models.zone import Zone
from app.db.schemas.zone import ZoneCreate, ZoneUpdate, ZoneRead

def create_zone(db: Session, zone: ZoneCreate) -> Zone:
    db_zone = Zone(**zone.model_dump())
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone

def get_zones(db: Session, skip: int = 0, limit: int = 100) -> List[Zone]:
    return db.query(Zone).offset(skip).limit(limit).all()

def get_zones_by_camera(db: Session, camera_id: int) -> List[Zone]:
    return db.query(Zone).filter(Zone.camera_id == camera_id).all()

def get_zone(db: Session, zone_id: int) -> Optional[Zone]:
    return db.query(Zone).filter(Zone.id == zone_id).first()

def update_zone(db: Session, zone_id: int, zone_update: ZoneUpdate) -> Optional[Zone]:
    db_zone = get_zone(db, zone_id)
    if not db_zone:
        return None
    
    update_data = zone_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_zone, field, value)
    
    db.commit()
    db.refresh(db_zone)
    return db_zone

def delete_zone(db: Session, zone_id: int) -> bool:
    db_zone = get_zone(db, zone_id)
    if not db_zone:
        return False
    
    db.delete(db_zone)
    db.commit()
    return True
