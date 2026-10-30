"""Application schemas"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ApplicationCreate(BaseModel):
    """Create application"""
    user_id: str
    job_id: str


class ApplicationResponse(BaseModel):
    """Application response"""
    id: str
    user_id: str
    job_id: str
    compatibility_score: Optional[float]
    status: str
    submitted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    """Application list response"""
    total: int
    items: List[ApplicationResponse]
    page: int
    page_size: int


class ApplicationStatusUpdate(BaseModel):
    """Update application status"""
    status: str
    notes: Optional[str] = None
