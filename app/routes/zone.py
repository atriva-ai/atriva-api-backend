from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..db.crud import zone as crud_zone
from ..db.schemas import zone as schema_zone

router = APIRouter(
    prefix="/api/v1/zones",
    tags=["zones"]
)

@router.post("/", response_model=schema_zone.ZoneRead)
def create_zone(zone: schema_zone.ZoneCreate, db: Session = Depends(get_db)):
    return crud_zone.create_zone(db, zone)

@router.get("/", response_model=List[schema_zone.ZoneRead])
def list_zones(db: Session = Depends(get_db)):
    return crud_zone.get_zones(db)

@router.get("/{zone_id}", response_model=schema_zone.ZoneRead)
def get_zone(zone_id: int, db: Session = Depends(get_db)):
    db_zone = crud_zone.get_zone(db, zone_id)
    if not db_zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return db_zone

@router.put("/{zone_id}", response_model=schema_zone.ZoneRead)
def update_zone(zone_id: int, zone: schema_zone.ZoneUpdate, db: Session = Depends(get_db)):
    db_zone = crud_zone.update_zone(db, zone_id, zone)
    if not db_zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return db_zone

@router.delete("/{zone_id}")
def delete_zone(zone_id: int, db: Session = Depends(get_db)):
    success = crud_zone.delete_zone(db, zone_id)
    if not success:
        raise HTTPException(status_code=404, detail="Zone not found")
    return {"message": "Zone deleted"}
