"""Job filtering and matching routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database.database import get_db
from app.models.job import Job
from app.models.user import UserProfile
from app.models.resume import Resume
from app.models.application import Application
from app.services.job_matching_service import job_matching_service
from app.services.ai_service import ai_service
import json
import uuid

router = APIRouter(prefix="/api/matching", tags=["matching"])

# Fallback skills used when the user has no parsed resume yet
DEFAULT_CANDIDATE_SKILLS = ["Python", "JavaScript", "SQL", "Git", "REST API"]


def _candidate_skills_for(user, db) -> list[str]:
    """Derive candidate skills from the latest verified/parsed resume if available."""
    resume = (
        db.query(Resume)
        .filter(Resume.user_id == user.id)
        .order_by(Resume.updated_at.desc())
        .first()
    )
    if resume and resume.skills:
        try:
            skills = json.loads(resume.skills) or []
            if isinstance(skills, list):
                # Filter into keyword-ish strings, drop resume section names
                cleaned = [str(s).strip() for s in skills if s]
                return cleaned or DEFAULT_CANDIDATE_SKILLS
        except (json.JSONDecodeError, TypeError):
            pass
    return DEFAULT_CANDIDATE_SKILLS


def _candidate_profile(user: UserProfile, db: Session) -> dict:
    """Build a candidate profile dict from the user + their latest resume."""
    skills = _candidate_skills_for(user, db)
    profile = {
        "name": user.name or "",
        "email": user.email or "",
        "phone": user.phone or "",
        "location": user.location or "",
        "is_fresh_graduate": user.is_fresh_graduate,
        "years_experience": 0 if user.is_fresh_graduate else 1,
        "minimum_salary": 25000,
        "skills": skills,
    }
    return profile


@router.post("/score/{user_id}/{job_id}")
async def score_job(
    user_id: str,
    job_id: str,
    db: Session = Depends(get_db)
):
    """Calculate job compatibility score"""
    # Get user and job
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Build candidate profile (skills derived from resume when available)
    candidate_profile = _candidate_profile(user, db)
    candidate_skills = candidate_profile["skills"]

    # Get matching score
    job_data = {
        "title": job.title,
        "company": job.company,
        "description": job.description,
        "requirements": job.requirements or "",
        "location": job.location,
        "is_remote": job.is_remote,
        "salary_min": job.salary_min,
        "experience_level": job.experience_level or ""
    }

    score_result = job_matching_service.calculate_compatibility_score(
        job_data,
        candidate_profile,
        candidate_skills
    )

    # Save to application if not already exists
    existing_app = db.query(Application).filter(
        and_(Application.user_id == user_id, Application.job_id == job_id)
    ).first()

    if existing_app:
        # Update existing application
        existing_app.compatibility_score = score_result["score"]
        existing_app.matching_skills = json.dumps(score_result["matching_skills"])
        existing_app.missing_skills = json.dumps(score_result["missing_skills"])
        existing_app.matching_explanation = score_result["explanation"]
    else:
        # Create new application
        app = Application(
            id=str(uuid.uuid4()),
            user_id=user_id,
            job_id=job_id,
            status="discovered",
            compatibility_score=score_result["score"],
            matching_skills=json.dumps(score_result["matching_skills"]),
            missing_skills=json.dumps(score_result["missing_skills"]),
            matching_explanation=score_result["explanation"]
        )
        db.add(app)
    
    db.commit()
    
    return {
        "job_id": job_id,
        "score": score_result["score"],
        "decision": score_result["decision"],
        "explanation": score_result["explanation"],
        "matching_skills": score_result["matching_skills"],
        "missing_skills": score_result["missing_skills"],
        "factors": score_result["factors"]
    }


@router.post("/batch-score/{user_id}")
async def batch_score_jobs(
    user_id: str,
    filters: dict = None,
    db: Session = Depends(get_db)
):
    """Score all matching jobs for a user"""
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get unfiltered jobs
    query = db.query(Job).filter(Job.is_filtered_out == False)
    
    if filters:
        if filters.get("min_salary"):
            query = query.filter(
                (Job.salary_min >= filters["min_salary"]) | (Job.salary_min == None)
            )
        if filters.get("remote_only"):
            query = query.filter(Job.is_remote == True)
        if filters.get("location"):
            query = query.filter(
                (Job.location.contains(filters["location"])) | (Job.is_remote == True)
            )
    
    jobs = query.limit(50).all()
    
    scored_jobs = []
    for job in jobs:
        try:
            # Score each job
            candidate_profile = {
                "is_fresh_graduate": user.is_fresh_graduate,
                "years_experience": 0,
                "minimum_salary": 25000
            }
            candidate_skills = ["Python", "JavaScript", "SQL"]
            
            job_data = {
                "title": job.title,
                "company": job.company,
                "description": job.description,
                "requirements": job.requirements or "",
                "is_remote": job.is_remote,
                "salary_min": job.salary_min,
                "experience_level": job.experience_level or ""
            }
            
            score_result = job_matching_service.calculate_compatibility_score(
                job_data,
                candidate_profile,
                candidate_skills
            )
            
            scored_jobs.append({
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "score": score_result["score"],
                "decision": score_result["decision"],
                "location": job.location,
                "is_remote": job.is_remote
            })
        
        except Exception as e:
            print(f"Error scoring job {job.id}: {e}")
    
    # Sort by score descending
    scored_jobs.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "total_scored": len(scored_jobs),
        "jobs": scored_jobs
    }


@router.get("/recommendations/{user_id}")
async def get_recommendations(
    user_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get job recommendations for user"""
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get top-scored applications
    applications = db.query(Application).filter(
        Application.user_id == user_id
    ).order_by(
        Application.compatibility_score.desc()
    ).limit(limit).all()
    
    recommendations = []
    for app in applications:
        job = db.query(Job).filter(Job.id == app.job_id).first()
        if job:
            recommendations.append({
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "is_remote": job.is_remote,
                "score": app.compatibility_score,
                "explanation": app.matching_explanation,
                "status": app.status
            })
    
    return {
        "total": len(recommendations),
        "recommendations": recommendations
    }
