#tenabot/bot/models.py
from datetime import datetime, date, timezone
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Boolean, Text, JSON, Date, Enum, Float,UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base


Base = declarative_base()

# --- 1. User Model (The added table) ---
class User(Base):
    __tablename__ = "users"

    # Core Fields from your Django model
    id = Column(Integer, primary_key=True, autoincrement=True) # Assumed primary key for FK
    telegram_id = Column(String(50), unique=True, nullable=False) # Your unique identifier
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(150), unique=True, nullable=True)
    avatar_url = Column(String(255), nullable=True)
    
    # Status and Time Fields
    is_active = Column(Boolean, default=True)
    is_staff = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships (to complete the two-way mapping)
    resumes = relationship("Resume", back_populates="user")
    usage = relationship("UsageTracker", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User id={self.id} telegram={self.telegram_id}>"

# --- 2. Resume Model ---
class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String(255), nullable=False)
    job_title = Column(String(150), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)

    # Relationships
    resume_info = relationship("ResumeInfo", back_populates="resume", uselist=False)
    user = relationship("User", back_populates="resumes") # Links to the User model above

    def __repr__(self):
        return f"<Resume job={self.job_title} user={self.user_id}>"

# --- 3. ResumeInfo Model ---
class ResumeInfo(Base):
    __tablename__ = "resume_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    phone = Column(String(50))
    email = Column(String(150))
    linkedin = Column(String(255))
    position = Column(String(150))
    education_level = Column(String(100))
    work_history = Column(JSON)
    skills = Column(JSON)
    core_values = Column(JSON)
    structured_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow) 

    # Relationships
    resume = relationship("Resume", back_populates="resume_info")

    def __repr__(self):
        return f"<ResumeInfo resume={self.resume_id}>"

# --- 4. UsageTracker Model ---
class UsageTracker(Base):
    __tablename__ = "usage_tracker"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 1. REMOVED unique=True here. It is now only a ForeignKey.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) 
    
    date = Column(Date, default=date.today, nullable=False)
    count = Column(Integer, default=0, nullable=False)

    # Relationships
    # Note: Use 'usage_tracker' as the back_populates name for clarity/consistency
    user = relationship("User", back_populates="usage_trackers") 

    # 2. ADDED Composite Unique Constraint:
    # This ensures that a single user can only have ONE entry for a specific date.
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uq_user_date_unique'),
    )

    def __repr__(self):
        return f"<UsageTracker user_id={self.user_id} date={self.date} count={self.count}>"