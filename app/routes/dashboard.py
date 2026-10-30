"""Dashboard routes"""

import os

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.database import get_db
from app.models.job import Job
from app.models.user import UserProfile
from app.models.resume import Resume
from app.models.application import Application
from app.models.search import SearchRun
from app.models.settings import Settings
from app.services.ai_service import ai_service

router = APIRouter(tags=["dashboard"])

templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page (single-page web app)."""
    return templates.TemplateResponse(request, "index.html", {})


@router.get("/api/stats")
async def api_stats(db: Session = Depends(get_db)):
    """Aggregate statistics shown on the dashboard."""
    # Counts
    total_jobs = db.query(Job).count()
    active_jobs = db.query(Job).filter(Job.is_filtered_out == False).count()  # noqa: E712
    filtered_jobs = total_jobs - active_jobs
    total_users = db.query(UserProfile).count()
    total_resumes = db.query(Resume).count()
    total_applications = db.query(Application).count()

    # Application funnel
    status_counts = dict(
        db.query(Application.status, func.count(Application.id)).group_by(Application.status).all()
    )

    # Match distribution
    strong_matches = db.query(Application).filter(
        Application.compatibility_score >= 75
    ).count()

    # Recent activity
    recent_jobs = (
        db.query(Job).order_by(Job.discovered_at.desc()).limit(5).all()
    )
    recent_apps = (
        db.query(Application).order_by(Application.updated_at.desc()).limit(5).all()
    )
    recent_runs = (
        db.query(SearchRun).order_by(SearchRun.started_at.desc()).limit(5).all()
    )

    return {
        "jobs": {
            "total": total_jobs,
            "active": active_jobs,
            "filtered": filtered_jobs,
        },
        "users": total_users,
        "resumes": total_resumes,
        "applications": {
            "total": total_applications,
            "by_status": status_counts,
            "strong_matches": strong_matches,
        },
        "ai": ai_service.status(),
        "recent_jobs": [
            {
                "id": j.id,
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "is_remote": j.is_remote,
                "salary_min": j.salary_min,
                "salary_max": j.salary_max,
                "source": j.source,
                "is_filtered_out": j.is_filtered_out,
                "filter_reason": j.filter_reason,
                "discovered_at": j.discovered_at,
            }
            for j in recent_jobs
        ],
        "recent_applications": [
            {
                "id": a.id,
                "job_id": a.job_id,
                "user_id": a.user_id,
                "status": a.status,
                "compatibility_score": a.compatibility_score,
                "updated_at": a.updated_at,
            }
            for a in recent_apps
        ],
        "recent_searches": [
            {
                "id": r.id,
                "query": r.search_query,
                "sources": r.sources_used.split(",") if r.sources_used else [],
                "found": r.jobs_found,
                "created": r.jobs_created,
                "filtered": r.jobs_filtered,
                "status": r.status,
                "started_at": r.started_at,
            }
            for r in recent_runs
        ],
        "settings_enabled_sources": (
            db.query(Settings).first().enabled_sources.split(",")
            if db.query(Settings).first()
            else []
        ),
    }
