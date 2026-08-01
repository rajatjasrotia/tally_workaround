from sqlmodel import create_engine, SQLModel, Session
from pathlib import Path
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./backend/database.db")

# Ensure parent directory exists for sqlite file
if DATABASE_URL.startswith("sqlite"):
    db_path = Path(DATABASE_URL.replace("sqlite:///", ""))
    if not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)
