"""Search run model for tracking job searches"""

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class SearchRun(Base):
    """Track individual job search runs"""
    
    __tablename__ = "search_runs"
    
    id = Column(String, primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    user_id = Column(String, ForeignKey("user_profiles.id"), nullable=False, index=True)
    
    # Search information
    search_query = Column(String, nullable=True)
    sources_used = Column(String, nullable=False)  # Comma-separated list of sources
    
    # Results
    jobs_found = Column(Integer, default=0)
    jobs_filtered = Column(Integer, default=0)
    jobs_duplicates = Column(Integer, default=0)
    jobs_created = Column(Integer, default=0)
    
    # Status
    status = Column(String, default="running")  # running, completed, failed
    error_message = Column(String, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("UserProfile", back_populates="search_runs")
