"""Job schemas"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class JobCreate(BaseModel):
    """Create job"""
    title: str
    company: str
    description: str
    requirements: Optional[str] = None
    location: Optional[str] = None
    is_remote: bool = False
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "PHP"
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    source: str
    source_job_id: Optional[str] = None
    source_url: Optional[str] = None


class JobResponse(BaseModel):
    """Job response"""
    id: str
    title: str
    company: str
    description: str
    location: Optional[str]
    is_remote: bool
    salary_min: Optional[float]
    salary_max: Optional[float]
    employment_type: Optional[str]
    experience_level: Optional[str]
    source: str
    source_url: Optional[str]
    is_duplicate: bool
    is_filtered_out: bool
    filter_reason: Optional[str]
    discovered_at: datetime
    
    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Job list response with pagination"""
    total: int
    items: List[JobResponse]
    page: int
    page_size: int
