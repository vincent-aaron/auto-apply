"""User settings model"""

from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class Settings(Base):
    """User search and application settings"""
    
    __tablename__ = "settings"
    
    id = Column(String, primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    user_id = Column(String, ForeignKey("user_profiles.id"), unique=True, nullable=False, index=True)
    
    # Search preferences
    target_countries = Column(String, default="Philippines")  # Comma-separated
    allow_remote = Column(Boolean, default=True)
    allow_fresh_graduate = Column(Boolean, default=True)
    
    # Experience level
    min_experience_years = Column(Float, default=0)
    max_experience_years = Column(Float, nullable=True)
    
    # Salary
    minimum_salary = Column(Integer, default=25000)
    salary_currency = Column(String, default="PHP")
    
    # Application targets
    daily_application_target = Column(Integer, default=50)
    
    # Excluded categories (comma-separated)
    excluded_job_categories = Column(String, default="BPO,Call Center,Customer Service,Sales,Marketing,Network Technician")
    
    # Job sources to enable (comma-separated)
    enabled_sources = Column(String, default="indeed,jobstreet,kalibrr")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserProfile")
