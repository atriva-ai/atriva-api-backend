# routers/store.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.models.store import Store
from app.dependencies import get_db

router = APIRouter()

# Request schema
class StoreUpdate(BaseModel):
    name: str

@router.get("/api/store")
def get_store(db: Session = Depends(get_db)):
    store = db.query(Store).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return {"name": store.name}

@router.post("/api/store")
def set_store_name(payload: StoreUpdate, db: Session = Depends(get_db)):
    store = db.query(Store).first()
    if store:
        store.name = payload.name
    else:
        store = Store(name=payload.name)
        db.add(store)
    db.commit()
    db.refresh(store)
    return {"name": store.name}