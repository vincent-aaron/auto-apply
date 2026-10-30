"""Main FastAPI application"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import logging

from app.database.database import init_db
from app.config import settings
from app.services.ai_service import ai_service
from app.routes import (
    dashboard, users, jobs, applications, settings as settings_routes,
    resumes, search, matching, application_automation
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Job Application Automation Assistant",
    description="AI-assisted job discovery, matching, and application automation",
    version="0.1.0"
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Include routers
app.include_router(dashboard.router)
app.include_router(users.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(settings_routes.router)
app.include_router(resumes.router)
app.include_router(search.router)
app.include_router(matching.router)
app.include_router(application_automation.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting Job Application Automation Assistant...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "debug": settings.debug
    }


@app.get("/api/config")
async def get_config():
    """Get application configuration"""
    return {
        "enabled_sources": settings.enabled_sources,
        "excluded_categories": settings.excluded_categories_list,
        "daily_target": settings.daily_application_target,
        "minimum_salary": settings.minimum_salary_php,
        "country": settings.country,
        "allow_remote": settings.allow_remote,
        "allow_fresh_graduate": settings.allow_fresh_graduate,
        "ai": ai_service.status(),
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
