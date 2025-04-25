from sqlalchemy.orm import Session
from models.zone import Zone
from schemas.zone import ZoneCreate, ZoneUpdate

def create_zone(db: Session, zone: ZoneCreate):
    db_zone = Zone(**zone.dict())
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone

def get_zones(db: Session):
    return db.query(Zone).all()

def get_zone(db: Session, zone_id: int):
    return db.query(Zone).filter(Zone.id == zone_id).first()

def update_zone(db: Session, zone_id: int, zone: ZoneUpdate):
    db_zone = get_zone(db, zone_id)
    if not db_zone:
        return None
    for key, value in zone.dict(exclude_unset=True).items():
        setattr(db_zone, key, value)
    db.commit()
    db.refresh(db_zone)
    return db_zone

def delete_zone(db: Session, zone_id: int):
    db_zone = get_zone(db, zone_id)
    if db_zone:
        db.delete(db_zone)
        db.commit()
    return db_zone
