from fastapi import FastAPI
from app.routes import camera
from app.database import engine, Base
import time
import psycopg2

# Step 1: Retry DB connection before anything else
def wait_for_db():
    for i in range(10):
        try:
            conn = psycopg2.connect(
                dbname="your_db",
                user="your_user",
                password="your_password",
                host="db",  # docker-compose service name
                port="5432"
            )
            conn.close()
            print("✅ DB is ready.")
            break
        except psycopg2.OperationalError:
            print("⏳ Waiting for DB...")
            time.sleep(3)

wait_for_db()

# Step 2: Initialize DB models/tables
# Only create tables automatically in dev, not production
if os.getenv("ENV", "production") != "production":
    Base.metadata.create_all(bind=engine)

# Step 3: Initialize FastAPI app
app = FastAPI()

# Step 4: Include routes
app.include_router(camera.router, prefix="/api/cameras", tags=["Cameras"])
