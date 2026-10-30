"""Application automation routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.application import Application, ApplicationEvent
from app.models.job import Job
from app.models.user import UserProfile
from app.models.resume import Resume
from app.services.application_automation_service import application_automation_service
from app.services.ai_service import ai_service
import uuid
from datetime import datetime
import json

router = APIRouter(prefix="/api/applications", tags=["applications"])


def _latest_resume(db: Session, user_id: str):
    """Return the most recent resume record for a user (or None)."""
    return (
        db.query(Resume)
        .filter(Resume.user_id == user_id)
        .order_by(Resume.updated_at.desc())
        .first()
    )


@router.post("/{application_id}/generate-answers")
async def generate_application_answers(
    application_id: str,
    db: Session = Depends(get_db),
):
    """Generate AI answers for application questions."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    job = db.query(Job).filter(Job.id == application.job_id).first()
    user = db.query(UserProfile).filter(UserProfile.id == application.user_id).first()
    if not job or not user:
        raise HTTPException(status_code=404, detail="Job or user not found")

    # Build candidate profile (add skills from the parsed resume if available)
    resume = _latest_resume(db, user.id)
    skills = []
    if resume and resume.skills:
        import json as _json
        try:
            skills = _json.loads(resume.skills) or []
        except (ValueError, TypeError):
            skills = []

    candidate_profile = {
        "name": user.name,
        "location": user.location,
        "is_fresh_graduate": user.is_fresh_graduate,
        "email": user.email,
        "phone": user.phone,
        "skills": skills,
    }

    common_questions = [
        "Tell us about yourself and your experience.",
        "Why are you interested in this position?",
        "What are your key skills for this role?",
        "How would your previous experience help you succeed here?",
    ]

    generated_answers = await ai_service.generate_application_answers(
        candidate_profile,
        {
            "title": job.title,
            "company": job.company,
            "description": job.description,
        },
        common_questions,
    )

    if not ai_service.is_configured:
        extra = {
            "hint": ("No OPENROUTER_API_KEY configured. Answers were generated locally (free). "
                     "Get a free key - instructions in API_KEYS.md - then restart the app for AI answers."),
            "ai_enabled": False,
        }
    else:
        extra = {"ai_enabled": True}

    application.generated_answers = json.dumps(generated_answers)
    application.status = "answers_generated"

    event = ApplicationEvent(
        id=str(uuid.uuid4()),
        application_id=application_id,
        event_type="answers_generated",
        description=f"Generated {len(common_questions)} application answers",
        event_metadata=json.dumps({"questions_count": len(common_questions)}),
    )
    db.add(event)

    db.commit()

    return {
        "application_id": application_id,
        "status": "answers_generated",
        "answers": generated_answers,
        "message": "Application answers have been generated. Please review them before submission.",
        **extra,
    }


@router.post("/{application_id}/prepare")
async def prepare_application(
    application_id: str,
    db: Session = Depends(get_db),
):
    """Prepare application for submission (browser automation)."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    job = db.query(Job).filter(Job.id == application.job_id).first()
    user = db.query(UserProfile).filter(UserProfile.id == application.user_id).first()

    if not job or not user or not job.source_url:
        raise HTTPException(status_code=400, detail="Missing required information")

    # Prepare candidate info
    candidate_info = {
        "first_name": user.name.split()[0] if user.name else "",
        "last_name": " ".join(user.name.split()[1:]) if user.name else "",
        "email": user.email,
        "phone": user.phone,
    }

    # Attach the latest resume for auto-upload if available
    resume = _latest_resume(db, user.id)

    # Get generated answers
    generated_answers = json.loads(application.generated_answers or "{}")

    # Prepare application
    result = await application_automation_service.prepare_application(
        job.source_url,
        candidate_info,
        generated_answers,
        resume_path=resume.file_path if resume else None,
    )

    if result["status"] == "ready_for_review":
        application.status = result["status"]

        event = ApplicationEvent(
            id=str(uuid.uuid4()),
            application_id=application_id,
            event_type="prepared",
            description="Application form prepared for review (browser automation)"
        )
        db.add(event)
        db.commit()
    elif result["status"] == "error":
        # Record the attempt in events so the user can see what happened
        event = ApplicationEvent(
            id=str(uuid.uuid4()),
            application_id=application_id,
            event_type="prepare_failed",
            description=result.get("message", "Failed to prepare application")
        )
        db.add(event)
        db.commit()

    return result


@router.post("/{application_id}/submit")
async def submit_application(
    application_id: str,
    db: Session = Depends(get_db)
):
    """Mark application as submitted"""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application.status = "submitted"
    application.submitted_at = datetime.utcnow()
    
    event = ApplicationEvent(
        id=str(uuid.uuid4()),
        application_id=application_id,
        event_type="submitted",
        description="Application submitted by user"
    )
    db.add(event)
    db.commit()
    
    return {
        "application_id": application_id,
        "status": "submitted",
        "submitted_at": application.submitted_at,
        "message": "Application submitted successfully! We will track its status."
    }


@router.get("/{application_id}/status")
async def get_application_status(
    application_id: str,
    db: Session = Depends(get_db)
):
    """Get application status and history"""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    job = db.query(Job).filter(Job.id == application.job_id).first()
    events = db.query(ApplicationEvent).filter(
        ApplicationEvent.application_id == application_id
    ).order_by(ApplicationEvent.created_at).all()
    
    return {
        "application_id": application_id,
        "job_title": job.title if job else "Unknown",
        "company": job.company if job else "Unknown",
        "status": application.status,
        "compatibility_score": application.compatibility_score,
        "submitted_at": application.submitted_at,
        "events": [
            {
                "event_type": e.event_type,
                "description": e.description,
                "created_at": e.created_at
            }
            for e in events
        ]
    }
