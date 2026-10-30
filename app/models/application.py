"""Application model"""

from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class Application(Base):
    """Job application model"""
    
    __tablename__ = "applications"
    
    id = Column(String, primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    user_id = Column(String, ForeignKey("user_profiles.id"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    
    # Matching score
    compatibility_score = Column(Float, nullable=True)
    matching_skills = Column(Text, nullable=True)  # JSON
    missing_skills = Column(Text, nullable=True)  # JSON
    matching_explanation = Column(Text, nullable=True)
    
    # Status
    status = Column(String, default="discovered")  # discovered, preparing, ready_for_review, submitted, rejected
    
    # Application answers
    generated_answers = Column(Text, nullable=True)  # JSON
    
    # Submission tracking
    submitted_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserProfile", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    answers = relationship("ApplicationAnswer", back_populates="application", cascade="all, delete-orphan")
    events = relationship("ApplicationEvent", back_populates="application", cascade="all, delete-orphan")


class ApplicationAnswer(Base):
    """Application answer model"""
    
    __tablename__ = "application_answers"
    
    id = Column(String, primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    application_id = Column(String, ForeignKey("applications.id"), nullable=False, index=True)
    
    # Question and answer
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    is_generated = Column(String, default=True)  # Whether AI generated the answer
    
    # Verification
    is_verified = Column(String, default=False)
    verification_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    application = relationship("Application", back_populates="answers")


class ApplicationEvent(Base):
    """Track application events for auditing"""
    
    __tablename__ = "application_events"
    
    id = Column(String, primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    application_id = Column(String, ForeignKey("applications.id"), nullable=False, index=True)
    
    # Event information
    event_type = Column(String, nullable=False)  # created, answers_generated, submitted, rejected, etc.
    description = Column(Text, nullable=True)
    event_metadata = Column(Text, nullable=True)  # JSON
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    application = relationship("Application", back_populates="events")
