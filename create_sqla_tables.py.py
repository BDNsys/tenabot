# create_sqla_tables.py

# Import the engine and Base from your SQLAlchemy setup
from tenabot.db import engine


# Import all your models so SQLAlchemy knows about them
from bot.models import User, Resume, ResumeInfo, UsageTracker ,Base

print("Starting SQLAlchemy table creation...")

# Check if the 'users' table already exists (it should, from Django!)
# SQLAlchemy will skip tables that exist but will create the others.

# This command reads the metadata from all classes inheriting from Base
# and creates the corresponding tables if they don't exist.
Base.metadata.create_all(bind=engine) 

print("SQLAlchemy tables created successfully (resumes, resume_info, usage_tracker).")