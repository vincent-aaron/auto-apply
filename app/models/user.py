"""User profile model"""

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class UserProfile(Base):
    """User profile model"""
    
    __tablename__ = "user_profiles"
    
    id = Column(String, primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=True)
    
    # Profile information
    location = Column(String, nullable=True)  # City/province
    is_fresh_graduate = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    search_runs = relationship("SearchRun", back_populates="user", cascade="all, delete-orphan")
