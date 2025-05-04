from sqlalchemy.orm import Session
from app.db.models.camera import Camera
from app.db.models.zone import Zone
from app.db.schemas.camera import CameraCreate, CameraUpdate

def create_camera(db: Session, camera: CameraCreate):
    db_camera = Camera(**camera.dict(exclude={"zone_ids"}))
    if camera.zone_ids:
        db_camera.zones = db.query(Zone).filter(Zone.id.in_(camera.zone_ids)).all()
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    return db_camera

def get_cameras(db: Session):
    return db.query(Camera).all()

def get_camera(db: Session, camera_id: int):
    return db.query(Camera).filter(Camera.id == camera_id).first()

def update_camera(db: Session, camera_id: int, camera: CameraUpdate):
    db_camera = get_camera(db, camera_id)
    if not db_camera:
        return None
    for key, value in camera.dict(exclude_unset=True, exclude={"zone_ids"}).items():
        setattr(db_camera, key, value)
    if camera.zone_ids:
        db_camera.zones = db.query(Zone).filter(Zone.id.in_(camera.zone_ids)).all()
    db.commit()
    db.refresh(db_camera)
    return db_camera

def delete_camera(db: Session, camera_id: int):
    db_camera = get_camera(db, camera_id)
    if db_camera:
        db.delete(db_camera)
        db.commit()
    return db_camera

# crud/camera.py
def update_camera_analytics(db: Session, camera_id: int, analytics_config: dict):
    db_camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if db_camera:
        db_camera.analytics_config = analytics_config
        db.commit()
        db.refresh(db_camera)
    return db_camera
