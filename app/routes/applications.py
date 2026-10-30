"""Application API routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database.database import get_db
from app.models.application import Application
from app.models.job import Job
from app.schemas.application import ApplicationCreate, ApplicationResponse, ApplicationStatusUpdate
import uuid


def _serialize_application(app: Application, db: Session) -> dict:
    """Serialize an application together with its job details."""
    job = db.query(Job).filter(Job.id == app.job_id).first()
    return {
        "id": app.id,
        "user_id": app.user_id,
        "job_id": app.job_id,
        "job_title": job.title if job else "Unknown",
        "company": job.company if job else "Unknown",
        "job_url": job.source_url if job else None,
        "location": job.location if job else None,
        "is_remote": job.is_remote if job else False,
        "salary_min": job.salary_min if job else None,
        "salary_max": job.salary_max if job else None,
        "compatibility_score": app.compatibility_score,
        "matching_skills": app.matching_skills,
        "missing_skills": app.missing_skills,
        "matching_explanation": app.matching_explanation,
        "status": app.status,
        "has_answers": bool(app.generated_answers),
        "submitted_at": app.submitted_at,
        "created_at": app.created_at,
        "updated_at": app.updated_at,
    }


router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(application: ApplicationCreate, db: Session = Depends(get_db)):
    """Create a new application"""
    # Check if application already exists
    existing = db.query(Application).filter(
        and_(Application.user_id == application.user_id, Application.job_id == application.job_id)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application already exists for this job"
        )

    db_application = Application(
        id=str(uuid.uuid4()),
        user_id=application.user_id,
        job_id=application.job_id,
        status="discovered"
    )
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application


@router.get("/")
async def list_all_applications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all applications (enriched with job info), newest first."""
    query = db.query(Application).order_by(Application.updated_at.desc())
    total = query.count()
    applications = query.offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [_serialize_application(a, db) for a in applications],
        "page": skip // limit if limit else 0,
        "page_size": limit,
    }


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(application_id: str, db: Session = Depends(get_db)):
    """Get application details"""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    return application


@router.get("/user/{user_id}")
async def list_user_applications(user_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List applications for a user (enriched with job info)."""
    query = db.query(Application).filter(Application.user_id == user_id).order_by(
        Application.updated_at.desc()
    )
    total = query.count()
    applications = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [_serialize_application(a, db) for a in applications],
        "page": skip // limit if limit else 0,
        "page_size": limit,
    }


@router.patch("/{application_id}")
async def update_application_status(
    application_id: str,
    update: ApplicationStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update application status"""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    application.status = update.status
    if update.notes:
        application.notes = update.notes

    db.commit()
    db.refresh(application)
    return _serialize_application(application, db)
