# init_db.py
from app.database import engine, SessionLocal, Base
from app.db.models.store import Store

def seed():
    db = SessionLocal()
    if not db.query(Store).first():
        db.add(Store(name="Default Store"))
        db.commit()
    db.close()

def init():
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created")
    seed()

if __name__ == "__main__":
    init()
