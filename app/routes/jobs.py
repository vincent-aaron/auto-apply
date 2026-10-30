"""Job API routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.job import Job
from app.schemas.job import JobCreate, JobResponse, JobListResponse
import uuid

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(job: JobCreate, db: Session = Depends(get_db)):
    """Create a new job listing"""
    # Generate source hash for deduplication
    import hashlib
    source_hash_input = f"{job.source}:{job.company}:{job.title}:{job.location or 'remote'}"
    source_hash = hashlib.md5(source_hash_input.encode()).hexdigest()
    
    # Check for duplicates
    existing_job = db.query(Job).filter(Job.source_hash == source_hash).first()
    if existing_job:
        # Update existing job
        existing_job.updated_at = __import__('datetime').datetime.utcnow()
        db.commit()
        db.refresh(existing_job)
        return existing_job
    
    db_job = Job(
        id=str(uuid.uuid4()),
        title=job.title,
        company=job.company,
        description=job.description,
        requirements=job.requirements,
        location=job.location,
        is_remote=job.is_remote,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        employment_type=job.employment_type,
        experience_level=job.experience_level,
        source=job.source,
        source_job_id=job.source_job_id,
        source_url=job.source_url,
        source_hash=source_hash
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get a job listing"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return job


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    skip: int = 0,
    limit: int = 20,
    source: str = None,
    is_remote: bool = None,
    is_filtered_out: bool = False,
    db: Session = Depends(get_db)
):
    """List jobs with filters"""
    query = db.query(Job).filter(Job.is_filtered_out == is_filtered_out)
    
    if source:
        query = query.filter(Job.source == source)
    
    if is_remote is not None:
        query = query.filter(Job.is_remote == is_remote)
    
    total = query.count()
    jobs = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": jobs,
        "page": skip // limit,
        "page_size": limit
    }


@router.patch("/{job_id}")
async def update_job_status(
    job_id: str,
    is_filtered_out: bool = None,
    filter_reason: str = None,
    db: Session = Depends(get_db)
):
    """Update job status"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if is_filtered_out is not None:
        job.is_filtered_out = is_filtered_out
    
    if filter_reason is not None:
        job.filter_reason = filter_reason
    
    db.commit()
    db.refresh(job)
    return job
