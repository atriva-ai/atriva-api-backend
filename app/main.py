from fastapi import FastAPI
from app.routes import camera, store, settings
from app.database import engine, Base
import time
import psycopg2
import os
from fastapi.middleware.cors import CORSMiddleware

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

# CORS configuration
origins = [
    "http://localhost:3000",     # Next.js development server
    "http://127.0.0.1:3000",    # Next.js development server alternative
    "http://frontend:3000",      # Docker service name
]

# Add production origins if in production
if os.getenv("ENV") == "production":
    origins.extend([
        # Add your production frontend URLs here
        # "https://your-production-domain.com",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Step 3: Include routes
try:
    app.include_router(camera.router, prefix="/api/v1/cameras", tags=["Cameras"])
except Exception as e:
    print("Failed to load camera routes:", e)

try:
    app.include_router(store.router, prefix="/api/v1/store", tags=["Store"])
except Exception as e:
    print("Failed to load store routes:", e)

try:
    app.include_router(settings.router, prefix="/api/v1/settings", tags=["Settings"])
except Exception as e:
    print("Failed to load settings routes:", e)

# @app.get("/")
# def health():
#    return {"ok": True}