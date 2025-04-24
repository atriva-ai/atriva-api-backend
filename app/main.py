from fastapi import FastAPI
from app.routes import camera
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(camera.router, prefix="/api/cameras", tags=["Cameras"])
