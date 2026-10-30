"""Settings API routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.settings import Settings
from app.models.user import UserProfile
from app.schemas.settings import SettingsUpdate, SettingsResponse
import uuid

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/{user_id}", response_model=SettingsResponse)
async def get_settings(user_id: str, db: Session = Depends(get_db)):
    """Get user settings"""
    settings = db.query(Settings).filter(Settings.user_id == user_id).first()
    
    if not settings:
        # Create default settings if they don't exist
        user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        settings = Settings(
            id=str(uuid.uuid4()),
            user_id=user_id
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings


@router.put("/{user_id}", response_model=SettingsResponse)
async def update_settings(user_id: str, settings_update: SettingsUpdate, db: Session = Depends(get_db)):
    """Update user settings"""
    settings = db.query(Settings).filter(Settings.user_id == user_id).first()
    
    if not settings:
        user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        settings = Settings(
            id=str(uuid.uuid4()),
            user_id=user_id
        )
        db.add(settings)
    
    update_data = settings_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    db.commit()
    db.refresh(settings)
    return settings
