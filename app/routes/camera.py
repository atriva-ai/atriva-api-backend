from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..db.models.camera import Camera as CameraModel
from ..db.schemas.camera import CameraCreate, CameraUpdate, CameraInDB
from ..db.crud import camera as camera_crud

router = APIRouter(
    prefix="/api/v1/cameras",
    tags=["cameras"]
)

@router.get("/", response_model=List[CameraInDB])
def list_cameras(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    List all cameras
    """
    return camera_crud.get_cameras(db, skip=skip, limit=limit)

@router.post("/", response_model=CameraInDB)
def create_camera(
    camera: CameraCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new camera
    """
    return camera_crud.create_camera(db=db, camera=camera)

@router.get("/{camera_id}", response_model=CameraInDB)
def get_camera(
    camera_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific camera by ID
    """
    db_camera = camera_crud.get_camera(db, camera_id=camera_id)
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    return db_camera

@router.put("/{camera_id}", response_model=CameraInDB)
def update_camera(
    camera_id: int,
    camera_update: CameraUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a camera
    """
    db_camera = camera_crud.update_camera(db, camera_id=camera_id, camera_update=camera_update)
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    return db_camera

@router.delete("/{camera_id}")
def delete_camera(
    camera_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a camera
    """
    success = camera_crud.delete_camera(db, camera_id=camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {"message": "Camera deleted successfully"}

# @router.put("/{camera_id}/analytics", response_model=CameraRead)
# def set_camera_analytics(camera_id: int, analytics_config: dict, db: Session = Depends(get_db)):
#     return crud_camera.update_camera_analytics(db, camera_id, analytics_config)
