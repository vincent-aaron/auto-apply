"""Resume model"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class Resume(Base):
    """Resume model"""
    
    __tablename__ = "resumes"
    
    id = Column(String, primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    user_id = Column(String, ForeignKey("user_profiles.id"), nullable=False, index=True)
    
    # File information
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, docx
    
    # Extracted information
    raw_text = Column(Text, nullable=True)
    
    # Structured data (JSON-like, will be stored as text)
    education = Column(Text, nullable=True)  # JSON
    experience = Column(Text, nullable=True)  # JSON
    skills = Column(Text, nullable=True)  # JSON
    certifications = Column(Text, nullable=True)  # JSON
    languages = Column(Text, nullable=True)  # JSON
    projects = Column(Text, nullable=True)  # JSON
    
    # Status
    is_verified = Column(String, default="pending")  # pending, verified, rejected
    verification_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserProfile", back_populates="resumes")
