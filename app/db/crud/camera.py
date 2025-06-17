from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.models.camera import Camera
from app.db.models.zone import Zone
from app.db.schemas.camera import CameraCreate, CameraUpdate

def create_camera(db: Session, camera: CameraCreate) -> Camera:
    db_camera = Camera(**camera.model_dump())
    if camera.zone_ids:
        db_camera.zones = db.query(Zone).filter(Zone.id.in_(camera.zone_ids)).all()
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    return db_camera

def get_cameras(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    is_active: Optional[bool] = None
) -> List[Camera]:
    query = db.query(Camera)
    if is_active is not None:
        query = query.filter(Camera.is_active == is_active)
    return query.offset(skip).limit(limit).all()

def get_camera(db: Session, camera_id: int) -> Optional[Camera]:
    return db.query(Camera).filter(Camera.id == camera_id).first()

def update_camera(
    db: Session, 
    camera_id: int, 
    camera_update: CameraUpdate
) -> Optional[Camera]:
    db_camera = get_camera(db, camera_id)
    if not db_camera:
        return None

    update_data = camera_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_camera, field, value)

    if camera_update.zone_ids:
        db_camera.zones = db.query(Zone).filter(Zone.id.in_(camera_update.zone_ids)).all()

    db.commit()
    db.refresh(db_camera)
    return db_camera

def delete_camera(db: Session, camera_id: int) -> bool:
    db_camera = get_camera(db, camera_id)
    if not db_camera:
        return False

    db.delete(db_camera)
    db.commit()
    return True

# crud/camera.py
def update_camera_analytics(db: Session, camera_id: int, analytics_config: dict):
    db_camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if db_camera:
        db_camera.analytics_config = analytics_config
        db.commit()
        db.refresh(db_camera)
    return db_camera

def get_cameras_count(db: Session, is_active: Optional[bool] = None) -> int:
    query = db.query(Camera)
    if is_active is not None:
        query = query.filter(Camera.is_active == is_active)
    return query.count()
