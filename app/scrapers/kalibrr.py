"""Kalibrr job scraper"""

from typing import List, Dict, Any
from app.scrapers.base import BaseJobConnector
import logging

logger = logging.getLogger(__name__)


class KalibrrScraper(BaseJobConnector):
    """Scraper for Kalibrr.com"""
    
    def __init__(self):
        super().__init__("Kalibrr")
        self.base_url = "https://www.kalibrr.com"
    
    async def search(self, query: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for jobs on Kalibrr"""
        jobs = []
        
        try:
            # Mock data for demo
            mock_jobs = await self._get_mock_kalibrr_jobs(query, filters)
            jobs.extend(mock_jobs)
        
        except Exception as e:
            logger.error(f"Error scraping Kalibrr: {e}")
        
        return jobs
    
    async def _get_mock_kalibrr_jobs(self, query: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return mock job data"""
        return [
            self.normalize_job(
                title="Frontend Developer (React)",
                company="Creative Digital Agency",
                description="Looking for a talented frontend developer with React experience...",
                source_job_id="kb_98765",
                location="Cebu, Philippines",
                is_remote=True,
                salary_min=28000,
                salary_max=40000,
                salary_currency="PHP",
                employment_type="Full-time",
                experience_level="Junior",
                source_url="https://www.kalibrr.com/job/98765",
                requirements="React, JavaScript, HTML/CSS, Git"
            ),
            self.normalize_job(
                title="Full Stack Developer",
                company="E-commerce Platform",
                description="We need a full stack developer to help build our platform...",
                source_job_id="kb_98766",
                location="Davao, Philippines",
                is_remote=False,
                salary_min=32000,
                salary_max=45000,
                salary_currency="PHP",
                employment_type="Full-time",
                experience_level="Entry-level to Mid-level",
                source_url="https://www.kalibrr.com/job/98766",
                requirements="React, Node.js, MongoDB, AWS"
            ),
            self.normalize_job(
                title="Software Developer - Recent Grad Welcome",
                company="Innovation Lab",
                description="Join our innovative team as a Software Developer. Recent graduates encouraged to apply...",
                source_job_id="kb_98767",
                location="Iloilo, Philippines",
                is_remote=True,
                salary_min=24000,
                salary_max=32000,
                salary_currency="PHP",
                employment_type="Full-time",
                experience_level="Fresh Graduate",
                source_url="https://www.kalibrr.com/job/98767",
                requirements="Programming fundamentals, problem-solving"
            ),
        ]
