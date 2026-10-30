"""Resume API routes"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.resume import Resume
from app.models.user import UserProfile
from app.schemas.resume import ResumeResponse, ResumeVerify
from app.services.resume_service import resume_service
import uuid
import os
from pathlib import Path
import json

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("/upload/{user_id}", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    user_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a resume"""
    # Check if user exists
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate file type
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["pdf", "docx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported"
        )
    
    try:
        # Create uploads directory if it doesn't exist
        uploads_dir = Path("uploads/resumes")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_id = str(uuid.uuid4())
        file_path = uploads_dir / f"{file_id}_{file.filename}"
        
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Create resume record
        db_resume = Resume(
            id=str(uuid.uuid4()),
            user_id=user_id,
            filename=file.filename,
            file_path=str(file_path),
            file_type=file_ext,
            is_verified="pending"
        )
        
        db.add(db_resume)
        db.commit()
        db.refresh(db_resume)
        
        return db_resume
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload resume: {str(e)}"
        )


@router.post("/{resume_id}/extract")
async def extract_resume_info(
    resume_id: str,
    db: Session = Depends(get_db)
):
    """Extract information from resume"""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    try:
        # Process resume
        result = await resume_service.process_resume(resume.file_path, resume.file_type)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process resume file"
            )
        
        # Extract raw text
        raw_text = result.get("raw_text", "")
        resume.raw_text = raw_text
        
        # Extract sections
        sections = resume_service.extract_sections(raw_text)
        resume.education = sections.get("education")
        resume.experience = sections.get("experience")
        resume.skills = sections.get("skills")
        resume.certifications = sections.get("certifications")
        resume.languages = sections.get("languages")
        resume.projects = sections.get("projects")
        
        db.commit()
        db.refresh(resume)
        
        return {
            "id": resume.id,
            "status": "extracted",
            "education": json.loads(resume.education or "[]"),
            "experience": json.loads(resume.experience or "[]"),
            "skills": json.loads(resume.skills or "[]"),
            "certifications": json.loads(resume.certifications or "[]"),
            "languages": json.loads(resume.languages or "[]"),
            "projects": json.loads(resume.projects or "[]"),
            "message": "Resume information extracted. Please verify the details."
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract resume info: {str(e)}"
        )


@router.post("/{resume_id}/verify", response_model=ResumeResponse)
async def verify_resume(
    resume_id: str,
    verification: ResumeVerify,
    db: Session = Depends(get_db)
):
    """Verify extracted resume information"""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    resume.is_verified = verification.is_verified
    resume.verification_notes = verification.verification_notes
    
    db.commit()
    db.refresh(resume)
    
    return resume


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: str, db: Session = Depends(get_db)):
    """Get resume details"""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    return resume


@router.get("/user/{user_id}")
async def list_user_resumes(user_id: str, db: Session = Depends(get_db)):
    """List all resumes for a user"""
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
    return {
        "total": len(resumes),
        "items": resumes
    }
