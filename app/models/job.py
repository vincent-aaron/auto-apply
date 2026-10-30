"""Job and skill models"""

from sqlalchemy import Column, String, Text, DateTime, Float, Boolean, ForeignKey, Table, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


# Association table for Job and Skill relationship
job_skills = Table(
    'job_skills',
    Base.metadata,
    Column('job_id', String, ForeignKey('jobs.id'), primary_key=True),
    Column('skill_id', String, ForeignKey('skills.id'), primary_key=True)
)


class Skill(Base):
    """Skill model"""
    
    __tablename__ = "skills"
    
    id = Column(String, primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    name = Column(String, unique=True, nullable=False, index=True)
    category = Column(String, nullable=True)  # programming, framework, tool, etc.
    
    # Relationships
    jobs = relationship("Job", secondary=job_skills, back_populates="required_skills")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Job(Base):
    """Job listing model"""
    
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    
    # Job information
    title = Column(String, nullable=False, index=True)
    company = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)
    
    # Location and remote
    location = Column(String, nullable=True)
    is_remote = Column(Boolean, default=False)
    
    # Compensation
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String, default="PHP")
    
    # Employment details
    employment_type = Column(String, nullable=True)  # Full-time, Contract, Internship, etc.
    experience_level = Column(String, nullable=True)  # Entry-level, Mid-level, Senior, etc.
    
    # Source information
    source = Column(String, nullable=False, index=True)  # linkedin, indeed, jobstreet, etc.
    source_job_id = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    
    # Deduplication
    source_hash = Column(String, unique=True, nullable=False, index=True)
    
    # Status
    is_duplicate = Column(Boolean, default=False)
    is_filtered_out = Column(Boolean, default=False)
    filter_reason = Column(String, nullable=True)
    
    # Timestamps
    discovered_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    required_skills = relationship("Skill", secondary=job_skills, back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
