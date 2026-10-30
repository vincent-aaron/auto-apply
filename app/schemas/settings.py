"""Settings schemas"""

from pydantic import BaseModel
from typing import Optional


class SettingsUpdate(BaseModel):
    """Update settings"""
    target_countries: Optional[str] = None
    allow_remote: Optional[bool] = None
    allow_fresh_graduate: Optional[bool] = None
    minimum_salary: Optional[int] = None
    daily_application_target: Optional[int] = None
    excluded_job_categories: Optional[str] = None
    enabled_sources: Optional[str] = None


class SettingsResponse(BaseModel):
    """Settings response"""
    id: str
    user_id: str
    target_countries: str
    allow_remote: bool
    allow_fresh_graduate: bool
    minimum_salary: int
    daily_application_target: int
    excluded_job_categories: str
    enabled_sources: str
    
    class Config:
        from_attributes = True
