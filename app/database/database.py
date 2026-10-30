"""Database configuration and session management"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.database.base import Base

# Create database engine
if settings.database_url.startswith("sqlite"):
    # SQLite requires check_same_thread=False
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        echo=settings.debug
    )
else:
    engine = create_engine(
        settings.database_url,
        echo=settings.debug
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    # Import models to register them with Base
    from app.models.user import UserProfile
    from app.models.resume import Resume
    from app.models.job import Job, Skill
    from app.models.application import Application, ApplicationAnswer, ApplicationEvent
    from app.models.settings import Settings as SettingsModel
    from app.models.search import SearchRun
    
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")


if __name__ == "__main__":
    init_db()
