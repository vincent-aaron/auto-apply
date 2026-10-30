"""Resume schemas"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class ResumeUpload(BaseModel):
    """Resume upload request"""
    filename: str
    file_type: str  # pdf, docx


class ResumeResponse(BaseModel):
    """Resume response"""
    id: str
    user_id: str
    filename: str
    file_type: str
    is_verified: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ResumeVerify(BaseModel):
    """Resume verification"""
    is_verified: str  # verified or rejected
    verification_notes: Optional[str] = None
