from fastapi import FastAPI
from app.routes import camera, store
from app.database import engine, Base
import time
import psycopg2
import os

# Step 1: Initialize DB models/tables
# Only create tables automatically in dev, not production
if os.getenv("ENV", "production") != "production":
    Base.metadata.create_all(bind=engine)

# Step 2: Initialize FastAPI app
app = FastAPI(
    title="Retail Dashboard Backend",
    docs_url="/docs",           # default is "/docs"
    redoc_url="/redoc",         # default is "/redoc"
    openapi_url="/openapi.json" # default is "/openapi.json"
)

# Step 3: Include routes
try:
    app.include_router(camera.router, prefix="/api/cameras", tags=["Cameras"])
except Exception as e:
    print("Failed to load camera routes:", e)

try:
    app.include_router(store.router, prefix="/api/store", tags=["Store"])
except Exception as e:
    print("Failed to load store routes:", e)

# @app.get("/")
# def health():
#    return {"ok": True}