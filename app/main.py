from fastapi import FastAPI
from app.routes import store, settings, camera, zone, analytics, video_pipeline, ai_inference, alert_engine
from app.database import engine, Base
import time
import psycopg2
import os
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

# Import all models to ensure they are registered with SQLAlchemy
from app.db.models import Store, Settings, Camera, Zone, Analytics, AlertEngine

# Step 1: Initialize DB models/tables
# Only create tables automatically in dev, not production
if os.getenv("ENV", "production") != "production":
    print("Development mode: Creating tables if they don't exist...")
    # Create tables in correct order (only if they don't exist)
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")
    
    # Seed the database with initial data
    from app.init_db import seed
    seed()
    print("✅ Database seeded successfully")

# Step 2: Initialize FastAPI app
app = FastAPI(
    title="Retail Dashboard Backend",
    docs_url="/docs",           # default is "/docs"
    redoc_url="/redoc",         # default is "/redoc"
    openapi_url="/openapi.json" # default is "/openapi.json"
)

# CORS configuration
origins = [
    # Frontend origins
    "http://localhost:3000",     # Next.js development server
    "http://127.0.0.1:3000",    # Next.js development server alternative
    "http://frontend:3000",      # Docker service name
    
    # Nginx proxy origins (for requests coming through nginx)
    "http://localhost",          # nginx proxy
    "http://localhost:80",       # nginx proxy explicit port
    "http://127.0.0.1",         # nginx proxy alternative
    "http://127.0.0.1:80",      # nginx proxy explicit port
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
    app.include_router(camera.router)
except Exception as e:
    print("Failed to load camera routes:", e)

try:
    app.include_router(zone.router)
except Exception as e:
    print("Failed to load zone routes:", e)

try:
    app.include_router(store.router, prefix="/api/v1/store", tags=["Store"])
except Exception as e:
    print("Failed to load store routes:", e)

try:
    app.include_router(settings.router, prefix="/api/v1/settings", tags=["Settings"])
except Exception as e:
    print("Failed to load settings routes:", e)

try:
    app.include_router(analytics.router)
except Exception as e:
    print("Failed to load analytics routes:", e)

try:
    app.include_router(alert_engine.router)
except Exception as e:
    print("Failed to load alert engine routes:", e)

try:
    app.include_router(video_pipeline.router)
except Exception as e:
    print("Failed to load video pipeline routes:", e)

try:
    app.include_router(ai_inference.router)
except Exception as e:
    print("Failed to load AI inference routes:", e)

# @app.get("/")
# def health():
#    return {"ok": True}

@app.get("/health")
def health():
    """Health check endpoint for Docker health checks"""
    try:
        # Test database connection
        from app.database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "Retail Dashboard Backend API", "status": "running"}