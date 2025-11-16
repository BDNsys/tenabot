import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path#
from dotenv import load_dotenv

# Ensure the .env file is loaded at the start of the module execution
load_dotenv()
# from tenabot.config import settings  # your custom settings handler
BASE_DIR = Path(__file__).resolve().parent.parent
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST") # Use a default host if needed
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
# DATABASE_URL = f'sqlite:///{BASE_DIR}/db.sqlite3'
DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'




engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency-like helper
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()