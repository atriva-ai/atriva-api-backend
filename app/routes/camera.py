from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from crud import camera as crud_camera
from schemas import camera as schema_camera

router = APIRouter()schema_camera

@router.post("/", response_model=.CameraRead)
def create_camera(camera: schema_camera.CameraCreate, db: Session = Depends(get_db)):
    return crud_camera.create_camera(db, camera)

@router.get("/", response_model=list[schema_camera.CameraOut])
def list_cameras(db: Session = Depends(get_db)):
    return crud_camera.get_cameras(db)

@router.get("/{camera_id}", response_model=schema_camera.CameraRead)
def get_camera(camera_id: int, db: Session = Depends(get_db)):
    db_camera = crud_camera.get_camera(db, camera_id)
    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return db_camera

@router.put("/{camera_id}", response_model=schema_camera.CameraRead)
def update_camera(camera_id: int, camera: schema_camera.CameraUpdate, db: Session = Depends(get_db)):
    return crud_camera.update_camera(db, camera_id, camera)

@router.delete("/{camera_id}")
def delete_camera(camera_id: int, db: Session = Depends(get_db)):
    crud_camera.delete_camera(db, camera_id)
    return {"message": "Camera deleted"}

@router.put("/{camera_id}/analytics", response_model=CameraRead)
def set_camera_analytics(camera_id: int, analytics_config: dict, db: Session = Depends(get_db)):
    return crud_camera.update_camera_analytics(db, camera_id, analytics_config)
