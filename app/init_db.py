# init_db.py
from app.database import engine, SessionLocal, Base
from app.db.models.store import Store
from app.db.models.settings import Settings
from app.db.models.camera import Camera
from app.db.models.analytics import Analytics

def seed():
    db = SessionLocal()
    # Seed store
    if not db.query(Store).first():
        db.add(Store(name="Default Store"))

    # Seed settings
    if not db.query(Settings).first():
        db.add(Settings(
            store_name="Default Store",
            store_description="Welcome to our store",
            store_timezone="UTC",
            store_language="en",
            store_theme="light",
            store_notifications_enabled=True,
            store_analytics_enabled=True
        ))

    # Seed analytics types
    predefined_analytics = [
        {
            "name": "People Counting",
            "type": "people_counting",
            "config": {
                "threshold": 0.5,
                "min_height": 100,
                "max_height": 300,
                "tracking_enabled": True
            },
            "is_active": True
        },
        {
            "name": "Dwell Time Analysis",
            "type": "dwell_time",
            "config": {
                "min_dwell_time": 5,
                "max_dwell_time": 300,
                "zone_detection": False,
                "heatmap_enabled": True
            },
            "is_active": True
        },
        {
            "name": "Demographic Analytics",
            "type": "demographic",
            "config": {
                "age_groups": ["18-25", "26-35", "36-45", "46-55", "55+"],
                "gender_detection": True,
                "emotion_analysis": True,
                "privacy_mode": True
            },
            "is_active": True
        }
    ]

    for analytics_data in predefined_analytics:
        existing = db.query(Analytics).filter(Analytics.type == analytics_data["type"]).first()
        if not existing:
            db.add(Analytics(**analytics_data))

    db.commit()
    db.close()

def init():
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created")
    seed()
    print("✅ Seed data added")

if __name__ == "__main__":
    init()
