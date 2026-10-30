"""Job search API routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.job import Job
from app.models.user import UserProfile
from app.models.search import SearchRun
from app.config import settings
from app.services.job_search_service import job_search_service
from app.services.job_filtering_service import job_filtering_service
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/jobs")
async def search_jobs(
    user_id: str,
    query: str,
    sources: list = None,
    location: str = "Philippines",
    db: Session = Depends(get_db),
):
    """
    Search for jobs across enabled sources.

    Args:
        user_id: User ID
        query: Search query
        sources: Job sources to search (optional; defaults to .env enabled sources)
        location: Job location
    """
    # Check if user exists
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # User settings override .env defaults when present
    from app.models.settings import Settings as UserSettings

    user_settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    excluded_categories = (
        [c.strip() for c in (user_settings.excluded_job_categories or "").split(",") if c.strip()]
        if user_settings and user_settings.excluded_job_categories
        else settings.excluded_categories_list
    )
    allow_remote = user_settings.allow_remote if user_settings else settings.allow_remote
    enabled = settings.enabled_sources
    if user_settings and user_settings.enabled_sources:
        user_enabled = [s.strip() for s in (user_settings.enabled_sources or "").split(",") if s.strip()]
        enabled = [s for s in user_enabled if s in enabled] or enabled

    # Only use sources enabled in settings (and requested)
    requested = [s for s in (sources or []) if s in enabled] if sources else enabled
    if not requested:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No job sources are enabled. Enable a source in Settings or .env (ENABLE_INDEED/ENABLE_JOBSTREET/ENABLE_KALIBRR).",
        )

    # Create search run record
    search_run = SearchRun(
        id=str(uuid.uuid4()),
        user_id=user_id,
        search_query=query,
        sources_used=",".join(requested),
        status="running",
    )
    db.add(search_run)
    db.commit()

    try:
        # Search for jobs
        filters = {"location": location}
        results = await job_search_service.search(query, requested, filters)

        # Save jobs, apply deterministic filters, and handle deduplication
        jobs_created = 0
        jobs_duplicates = 0
        jobs_filtered = 0
        all_jobs = results.get("jobs", [])

        for job_data in all_jobs:
            filtered_out, filter_reason = job_filtering_service.filter_job(
                job_data,
                excluded_categories=excluded_categories,
                allow_remote=allow_remote,
                country=settings.country,
            )

            # Check for existing job by source_hash
            existing_job = db.query(Job).filter(
                Job.source_hash == job_data["source_hash"]
            ).first()

            if existing_job:
                jobs_duplicates += 1
                existing_job.updated_at = datetime.utcnow()
                if filtered_out:
                    existing_job.is_filtered_out = True
                    existing_job.filter_reason = filter_reason
            else:
                db_job = Job(
                    id=str(uuid.uuid4()),
                    is_filtered_out=filtered_out,
                    filter_reason=filter_reason or None,
                    **job_data,
                )
                db.add(db_job)
                jobs_created += 1

            if filtered_out:
                jobs_filtered += 1

        db.commit()

        # Update search run
        search_run.status = "completed"
        search_run.jobs_found = len(all_jobs)
        search_run.jobs_created = jobs_created
        search_run.jobs_duplicates = jobs_duplicates
        search_run.jobs_filtered = jobs_filtered
        search_run.completed_at = datetime.utcnow()
        db.commit()

        return {
            "search_run_id": search_run.id,
            "total": len(all_jobs),
            "jobs_created": jobs_created,
            "jobs_duplicates": jobs_duplicates,
            "jobs_filtered": jobs_filtered,
            "sources": results.get("sources_searched", requested),
            "status": "completed",
        }

    except Exception as e:
        logger.error(f"Search error: {e}")
        search_run.status = "failed"
        search_run.error_message = str(e)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/jobs")
async def get_search_results(
    location: str = "Philippines",
    is_remote: bool = None,
    experience_level: str = None,
    salary_min: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get filtered job listings (jobs not filtered out by default)."""
    query = db.query(Job).filter(Job.is_filtered_out == False)  # noqa: E712

    # Apply filters
    if location:
        query = query.filter(
            (Job.location.contains(location) | (Job.is_remote == True))  # noqa: E712
        )
    if is_remote is not None:
        query = query.filter(Job.is_remote == is_remote)
    if experience_level:
        query = query.filter(Job.experience_level.contains(experience_level))
    if salary_min:
        query = query.filter((Job.salary_min >= salary_min) | (Job.salary_min == None))  # noqa: E711

    total = query.count()
    jobs = query.order_by(Job.discovered_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": jobs,
        "page": skip // limit if limit else 0,
        "page_size": limit,
    }


@router.get("/stats")
async def search_stats(db: Session = Depends(get_db)):
    """Aggregate search statistics."""
    runs = db.query(SearchRun).order_by(SearchRun.started_at.desc()).limit(20).all()
    return {
        "total_runs": db.query(SearchRun).count(),
        "total_jobs_found": sum(r.jobs_found or 0 for r in runs),
        "recent_runs": [
            {
                "id": r.id,
                "query": r.search_query,
                "sources": r.sources_used.split(","),
                "found": r.jobs_found,
                "created": r.jobs_created,
                "duplicates": r.jobs_duplicates,
                "filtered": r.jobs_filtered,
                "status": r.status,
                "error": r.error_message,
                "started_at": r.started_at,
                "completed_at": r.completed_at,
            }
            for r in runs
        ],
    }


@router.get("/run/{search_run_id}")
async def get_search_run(search_run_id: str, db: Session = Depends(get_db)):
    """Get search run details."""
    search_run = db.query(SearchRun).filter(SearchRun.id == search_run_id).first()
    if not search_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search run not found",
        )

    return {
        "id": search_run.id,
        "user_id": search_run.user_id,
        "search_query": search_run.search_query,
        "sources": search_run.sources_used.split(","),
        "jobs_found": search_run.jobs_found,
        "jobs_created": search_run.jobs_created,
        "jobs_duplicates": search_run.jobs_duplicates,
        "jobs_filtered": search_run.jobs_filtered,
        "status": search_run.status,
        "error": search_run.error_message,
        "started_at": search_run.started_at,
        "completed_at": search_run.completed_at,
    }