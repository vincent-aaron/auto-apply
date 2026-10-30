"""JobStreet Philippines scraper"""

from typing import List, Dict, Any
from app.scrapers.base import BaseJobConnector
import logging

logger = logging.getLogger(__name__)


class JobStreetScraper(BaseJobConnector):
    """Scraper for JobStreet.com.ph"""
    
    def __init__(self):
        super().__init__("JobStreet")
        self.base_url = "https://www.jobstreet.com.ph"
    
    async def search(self, query: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for jobs on JobStreet Philippines"""
        jobs = []
        
        try:
            # Mock data for demo
            mock_jobs = await self._get_mock_jobstreet_jobs(query, filters)
            jobs.extend(mock_jobs)
        
        except Exception as e:
            logger.error(f"Error scraping JobStreet: {e}")
        
        return jobs
    
    async def _get_mock_jobstreet_jobs(self, query: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return mock job data"""
        return [
            self.normalize_job(
                title="Web Developer (Entry Level)",
                company="StartUp Philippines",
                description="Exciting opportunity for a fresh web developer to work on innovative projects...",
                source_job_id="js_54321",
                location="Quezon City, Philippines",
                is_remote=False,
                salary_min=22000,
                salary_max=30000,
                salary_currency="PHP",
                employment_type="Full-time",
                experience_level="Entry-level",
                source_url="https://www.jobstreet.com.ph/job/54321",
                requirements="HTML, CSS, JavaScript, Bootstrap"
            ),
            self.normalize_job(
                title="Backend Developer",
                company="Fintech Solutions",
                description="Build scalable backend systems for our fintech platform...",
                source_job_id="js_54322",
                location="Makati, Philippines",
                is_remote=True,
                salary_min=35000,
                salary_max=50000,
                salary_currency="PHP",
                employment_type="Full-time",
                experience_level="Junior to Mid-level",
                source_url="https://www.jobstreet.com.ph/job/54322",
                requirements="Python, Django, PostgreSQL, Docker"
            ),
            self.normalize_job(
                title="Fresh Graduate Program - Software Development",
                company="Tech Giant Philippines",
                description="Join our prestigious Fresh Graduate Program and kickstart your IT career...",
                source_job_id="js_54323",
                location="BGC, Philippines",
                is_remote=False,
                salary_min=25000,
                salary_max=28000,
                salary_currency="PHP",
                employment_type="Full-time",
                experience_level="Fresh Graduate",
                source_url="https://www.jobstreet.com.ph/job/54323",
                requirements="BSCS/BSIT degree, problem-solving skills"
            ),
        ]
