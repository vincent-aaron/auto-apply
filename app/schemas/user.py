"""User schemas"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserProfileCreate(BaseModel):
    """Create user profile"""
    name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    is_fresh_graduate: bool = True


class UserProfileUpdate(BaseModel):
    """Update user profile"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    is_fresh_graduate: Optional[bool] = None


class UserProfileResponse(BaseModel):
    """User profile response"""
    id: str
    name: str
    email: str
    phone: Optional[str]
    location: Optional[str]
    is_fresh_graduate: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
