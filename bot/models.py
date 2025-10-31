
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Boolean, Text, JSON, Date, Enum, Float
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()
# Create your models here.
class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String(255), nullable=False)
    job_title = Column(String(150), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)

    resume_info = relationship("ResumeInfo", back_populates="resume", uselist=False)
    user = relationship("User", back_populates="resumes")

    def __repr__(self):
        return f"<Resume job={self.job_title} user={self.user_id}>"


class ResumeInfo(Base):
    __tablename__ = "resume_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    phone = Column(String(50))
    email = Column(String(150))
    linkedin = Column(String(255))
    position = Column(String(150))
    education_level = Column(String(100))
    work_history = Column(JSON)  # list of dicts like [{company, role, duration}]
    skills = Column(JSON)
    core_values = Column(JSON)
    structured_json = Column(JSON)  # Final parsed/structured version
    created_at = Column(DateTime, default=datetime.utcnow)

    resume = relationship("Resume", back_populates="resume_info")

    def __repr__(self):
        return f"<ResumeInfo resume={self.resume_id}>"


class UsageTracker(Base):
    __tablename__ = "usage_tracker"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    date = Column(Date, default=date.today)
    count = Column(Integer, default=0)

    user = relationship("User", back_populates="usage")

    def __repr__(self):
        return f"<UsageTracker user={self.user_id} count={self.count}>"