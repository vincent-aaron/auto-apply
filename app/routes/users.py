"""User API routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.user import UserProfile
from app.schemas.user import UserProfileCreate, UserProfileUpdate, UserProfileResponse
import uuid

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserProfileCreate, db: Session = Depends(get_db)):
    """Create a new user profile"""
    # Check if email already exists
    existing_user = db.query(UserProfile).filter(UserProfile.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    db_user = UserProfile(
        id=str(uuid.uuid4()),
        name=user.name,
        email=user.email,
        phone=user.phone,
        location=user.location,
        is_fresh_graduate=user.is_fresh_graduate
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user profile"""
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserProfileResponse)
async def update_user(user_id: str, user_update: UserProfileUpdate, db: Session = Depends(get_db)):
    """Update user profile"""
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user


@router.get("/")
async def list_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """List all users"""
    users = db.query(UserProfile).offset(skip).limit(limit).all()
    total = db.query(UserProfile).count()
    return {"total": total, "items": users, "skip": skip, "limit": limit}
