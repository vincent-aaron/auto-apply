"""Basic tests for the application"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.database import get_db
from app.database.base import Base


# Use in-memory SQLite for testing
# NOTE: StaticPool is required so every connection reuses the same in-memory DB.
from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestHealth:
    """Test application health checks"""
    
    def test_health_check(self):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_config_endpoint(self):
        """Test config endpoint"""
        response = client.get("/api/config")
        assert response.status_code == 200
        assert "enabled_sources" in response.json()


class TestUsers:
    """Test user endpoints"""
    
    def test_create_user(self):
        """Test creating a user"""
        response = client.post("/api/users/", json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "location": "Manila",
            "is_fresh_graduate": True
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
        assert "id" in data
    
    def test_create_duplicate_user(self):
        """Test creating duplicate user returns error"""
        user_data = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "is_fresh_graduate": True
        }
        
        # Create first user
        response1 = client.post("/api/users/", json=user_data)
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = client.post("/api/users/", json=user_data)
        assert response2.status_code == 400
    
    def test_get_user(self):
        """Test getting a user"""
        # Create user
        create_response = client.post("/api/users/", json={
            "name": "Test User",
            "email": "test@example.com"
        })
        user_id = create_response.json()["id"]
        
        # Get user
        get_response = client.get(f"/api/users/{user_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Test User"


class TestJobs:
    """Test job endpoints"""
    
    def test_create_job(self):
        """Test creating a job"""
        response = client.post("/api/jobs/", json={
            "title": "Junior Python Developer",
            "company": "Tech Corp",
            "description": "Looking for a junior developer",
            "location": "Manila",
            "is_remote": True,
            "source": "indeed"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Junior Python Developer"
        assert "id" in data
    
    def test_list_jobs(self):
        """Test listing jobs"""
        # Create a job first
        client.post("/api/jobs/", json={
            "title": "Python Developer",
            "company": "Tech Corp",
            "description": "A job",
            "source": "indeed"
        })
        
        # List jobs
        response = client.get("/api/jobs/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1


class TestApplications:
    """Test application endpoints"""
    
    def test_create_application(self):
        """Test creating an application"""
        # Create user
        user_response = client.post("/api/users/", json={
            "name": "Applicant",
            "email": "applicant@example.com"
        })
        user_id = user_response.json()["id"]
        
        # Create job
        job_response = client.post("/api/jobs/", json={
            "title": "Dev Job",
            "company": "Company",
            "description": "A dev job",
            "source": "indeed"
        })
        job_id = job_response.json()["id"]
        
        # Create application
        app_response = client.post("/api/applications/", json={
            "user_id": user_id,
            "job_id": job_id
        })

        assert app_response.status_code == 201
        assert app_response.json()["status"] == "discovered"


class TestJobMatchingService:
    """Test the deterministic matching service."""

    def test_strong_match_scoring(self):
        from app.services.job_matching_service import job_matching_service

        job = {
            "title": "Junior Python Developer",
            "company": "Tech Corp",
            "description": "Entry-level Python developer working on backend APIs with Flask.",
            "requirements": "Python, Flask, PostgreSQL",
            "location": "Manila",
            "is_remote": True,
            "salary_min": 25000,
            "experience_level": "Entry-level",
        }
        profile = {"is_fresh_graduate": True, "years_experience": 0, "minimum_salary": 25000}
        skills = ["Python", "JavaScript", "SQL", "Git", "REST API"]
        result = job_matching_service.calculate_compatibility_score(job, profile, skills)

        assert 0 <= result["score"] <= 100
        assert result["decision"] in ("strong_match", "match", "partial_match", "poor_match")
        assert "Python" in result["matching_skills"]
        assert isinstance(result["explanation"], str)

    def test_poor_match_low_score(self):
        from app.services.job_matching_service import job_matching_service

        job = {
            "title": "Senior Network Technician",
            "company": "Telco",
            "description": "Senior role requiring 5+ years of networking experience.",
            "requirements": "Cisco CCNA",
            "location": "US Only",
            "is_remote": False,
            "salary_min": 15000,
            "experience_level": "Senior",
        }
        profile = {"is_fresh_graduate": True, "years_experience": 0, "minimum_salary": 25000}
        result = job_matching_service.calculate_compatibility_score(
            job, profile, ["Python", "JavaScript"]
        )
        assert result["score"] < 60


class TestAIAnswersFallback:
    """AI answer generation must work WITHOUT an API key (free offline fallback)."""

    async def test_fallback_answers_are_truthful(self):
        from app.services.ai_service import AIService

        svc = AIService(api_key=None)  # no key -> fallback
        answers = await svc.generate_application_answers(
            {"name": "Juan Dela Cruz", "is_fresh_graduate": True},
            {"title": "Junior Web Developer", "company": "ABC Corp", "description": "Build web apps"},
            ["Tell us about yourself and your experience."],
        )
        assert len(answers) >= 1
        first = list(answers.values())[0]
        assert isinstance(first, str) and len(first) > 20
        # The fallback must not claim professional experience that doesn't exist
        assert "2 years of professional experience" not in first.lower()

    async def test_ai_disabled_flag_without_key(self, monkeypatch):
        from app.services.ai_service import ai_service

        # Force the offline (no-key) branch so this test is deterministic and
        # does not depend on whether a real OpenRouter key is set locally.
        monkeypatch.setattr(ai_service, "api_key", None)
        assert ai_service.is_configured is False

    async def test_extract_json_robustness(self):
        from app.services.ai_service import AIService

        assert AIService._extract_json('```json\n{"a": 1}\n```') == {"a": 1}
        assert AIService._extract_json('Text before {"x": [1,2]} and after') == {"x": [1, 2]}
        assert AIService._extract_json("no json here") == {}


class TestJobFilteringService:
    """Deterministic filtering rules from WORKFLOW sections 6-8."""

    def test_excluded_category(self):
        from app.services.job_filtering_service import job_filtering_service

        job = {"title": "Call Center Agent", "description": "BPO customer support", "requirements": ""}
        out, reason = job_filtering_service.filter_job(job, excluded_categories=["BPO", "Call Center"])
        assert out is True
        assert "Excluded" in reason

    def test_remote_accepted(self):
        from app.services.job_filtering_service import job_filtering_service

        job = {"title": "Developer", "description": "", "requirements": "",
               "location": "Remote", "is_remote": True}
        out, reason = job_filtering_service.filter_job(job, excluded_categories=[])
        assert out is False
        assert reason == ""

    def test_non_ph_location_rejected(self):
        from app.services.job_filtering_service import job_filtering_service

        job = {"title": "Developer", "description": "", "requirements": "",
               "location": "New York, USA", "is_remote": False}
        out, reason = job_filtering_service.filter_job(job, excluded_categories=[])
        assert out is True
        assert "not eligible" in reason.lower()


class TestSearchAndApplicationFlow:
    """End-to-end search -> score -> application -> answers flow (mock scrapers)."""

    def _create_user(self):
        import secrets

        resp = client.post("/api/users/", json={
            "name": "Flow Tester",
            "email": f"flow{secrets.token_hex(4)}@example.com",
            "is_fresh_graduate": True,
        })
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_search_saves_jobs(self):
        from app.models.job import Job

        uid = self._create_user()
        resp = client.post(
            "/api/search/jobs",
            params={"user_id": uid, "query": "Software Developer"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"

        with TestingSessionLocal() as db:
            total = db.query(Job).count()
        assert total >= 1

    def test_score_creates_application(self):
        from app.models.application import Application

        uid = self._create_user()
        job_resp = client.post("/api/jobs/", json={
            "title": "Junior Python Developer",
            "company": "Flow Corp",
            "description": "Entry-level Python backend work.",
            "requirements": "Python, Flask",
            "location": "Manila, Philippines",
            "is_remote": True,
            "source": "indeed",
            "source_job_id": "flow_job_2",
        })
        assert job_resp.status_code == 201
        job_id = job_resp.json()["id"]

        score_resp = client.post(f"/api/matching/score/{uid}/{job_id}")
        assert score_resp.status_code == 200
        assert score_resp.json()["score"] >= 0

        with TestingSessionLocal() as db:
            app = db.query(Application).filter(Application.job_id == job_id).first()
        assert app is not None
        assert app.user_id == uid

    def test_generate_answers_works_without_key(self, monkeypatch):
        from app.services.ai_service import ai_service
        from app.models.application import Application

        # Run this test in the offline (no-key) branch regardless of .env, so it
        # asserts the local fallback path deterministically (no live API call).
        monkeypatch.setattr(ai_service, "api_key", None)
        uid = self._create_user()
        job_resp = client.post("/api/jobs/", json={
            "title": "Web Developer",
            "company": "Web Co",
            "description": "Build websites",
            "source": "jobstreet",
            "source_job_id": "flow_web_1",
        })
        job_id = job_resp.json()["id"]

        score_resp = client.post(f"/api/matching/score/{uid}/{job_id}")
        assert score_resp.status_code == 200

        with TestingSessionLocal() as db:
            app = db.query(Application).filter(Application.job_id == job_id).first()
            app_id = app.id

        resp = client.post(f"/api/applications/{app_id}/generate-answers")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ai_enabled"] is False  # no key configured -> honest offline fallback
        assert len(data["answers"]) >= 1

    def test_application_status_lifecycle(self):
        uid = self._create_user()
        job_resp = client.post("/api/jobs/", json={
            "title": "Frontend Developer",
            "company": "UI Co",
            "description": "Build frontends",
            "source": "kalibrr",
            "source_job_id": "flow_ui_1",
        })
        job_id = job_resp.json()["id"]
        client.post(f"/api/matching/score/{uid}/{job_id}")

        with TestingSessionLocal() as db:
            from app.models.application import Application
            app = db.query(Application).filter(Application.job_id == job_id).first()
            app_id = app.id

        # Move to submitted
        resp = client.post(f"/api/applications/{app_id}/submit")
        assert resp.status_code == 200
        assert resp.json()["status"] == "submitted"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
