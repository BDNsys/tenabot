from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
# from tenabot.config import settings  # your custom settings handler
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = f'sqlite:///{BASE_DIR}/db.sqlite3'




engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency-like helper
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()