from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.db.schemas.alert_engine import AlertEngineCreate, AlertEngineUpdate, AlertEngine, CameraAlertEngineCreate
from app.db.crud import alert_engine as alert_engine_crud

router = APIRouter(
    prefix="/api/v1/alert-engines",
    tags=["alert-engines"]
)

@router.get("/", response_model=List[AlertEngine])
def get_all_alert_engines(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all alert engine configurations"""
    return alert_engine_crud.get_all_alert_engines(db, skip=skip, limit=limit)

@router.post("/", response_model=AlertEngine, status_code=status.HTTP_201_CREATED)
def create_alert_engine(
    alert_engine: AlertEngineCreate,
    db: Session = Depends(get_db)
):
    """Create a new alert engine configuration"""
    # Check if alert engine name already exists
    if alert_engine_crud.get_alert_engine_by_name(db, alert_engine.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert engine with this name already exists"
        )
    return alert_engine_crud.create_alert_engine(db, alert_engine)

@router.get("/{alert_engine_id}", response_model=AlertEngine)
def get_alert_engine(
    alert_engine_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific alert engine configuration"""
    db_alert_engine = alert_engine_crud.get_alert_engine(db, alert_engine_id)
    if not db_alert_engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert engine not found"
        )
    return db_alert_engine

@router.put("/{alert_engine_id}", response_model=AlertEngine)
def update_alert_engine(
    alert_engine_id: int,
    alert_engine: AlertEngineUpdate,
    db: Session = Depends(get_db)
):
    """Update an alert engine configuration"""
    db_alert_engine = alert_engine_crud.update_alert_engine(db, alert_engine_id, alert_engine)
    if not db_alert_engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert engine not found"
        )
    return db_alert_engine

@router.delete("/{alert_engine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert_engine(
    alert_engine_id: int,
    db: Session = Depends(get_db)
):
    """Delete an alert engine configuration"""
    success = alert_engine_crud.delete_alert_engine(db, alert_engine_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert engine not found"
        )

@router.get("/camera/{camera_id}", response_model=List[AlertEngine])
def get_camera_alert_engines(
    camera_id: int,
    db: Session = Depends(get_db)
):
    """Get all alert engine configurations for a specific camera"""
    return alert_engine_crud.get_camera_alert_engines(db, camera_id)

@router.post("/camera", status_code=status.HTTP_201_CREATED)
def add_alert_engine_to_camera(
    camera_alert_engine: CameraAlertEngineCreate,
    db: Session = Depends(get_db)
):
    """Add an alert engine configuration to a camera"""
    success = alert_engine_crud.add_alert_engine_to_camera(
        db, 
        camera_alert_engine.camera_id, 
        camera_alert_engine.alert_engine_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera or alert engine configuration not found"
        )
    return {"message": "Alert engine added to camera successfully"}

@router.delete("/camera/{camera_id}/{alert_engine_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_alert_engine_from_camera(
    camera_id: int,
    alert_engine_id: int,
    db: Session = Depends(get_db)
):
    """Remove an alert engine configuration from a camera"""
    success = alert_engine_crud.remove_alert_engine_from_camera(db, camera_id, alert_engine_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera or alert engine configuration not found"
        )

@router.patch("/{alert_engine_id}/toggle", response_model=AlertEngine)
def toggle_alert_engine_active(
    alert_engine_id: int,
    db: Session = Depends(get_db)
):
    """Toggle alert engine active status"""
    db_alert_engine = alert_engine_crud.toggle_alert_engine_active(db, alert_engine_id)
    if not db_alert_engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert engine not found"
        )
    return db_alert_engine 