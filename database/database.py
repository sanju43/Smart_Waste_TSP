from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "smart_waste_tsp.db"
engine = create_engine(f"sqlite:///{DB_PATH}", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    init_db()
    return SessionLocal()
