from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# from tenabot.config import settings  # your custom settings handler

DATABASE_URL = "postgresql://nazri:password@localhost:5432/tenadb"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency-like helper
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()