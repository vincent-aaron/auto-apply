"""Job search service"""

from typing import List, Dict, Any
from datetime import datetime
import asyncio
import logging

from app.scrapers.indeed import IndeedScraper
from app.scrapers.jobstreet import JobStreetScraper
from app.scrapers.kalibrr import KalibrrScraper

logger = logging.getLogger(__name__)


class JobSearchService:
    """Service for searching jobs across multiple sources"""
    
    def __init__(self):
        self.scrapers = {
            "indeed": IndeedScraper(),
            "jobstreet": JobStreetScraper(),
            "kalibrr": KalibrrScraper(),
        }
    
    async def search(
        self,
        query: str,
        sources: List[str],
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Search for jobs across multiple sources
        
        Args:
            query: Search query
            sources: List of sources to search (indeed, jobstreet, kalibrr)
            filters: Additional filters
        
        Returns:
            Search results with job listings
        """
        all_jobs = []
        
        # Fetch jobs from enabled sources
        tasks = []
        active_sources = []
        
        for source in sources:
            if source in self.scrapers:
                tasks.append(self.scrapers[source].search(query, filters))
                active_sources.append(source)
        
        if not tasks:
            return {
                "total": 0,
                "jobs": [],
                "sources_searched": []
            }
        
        # Run all searches concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        for source, result in zip(active_sources, results):
            if isinstance(result, Exception):
                logger.error(f"Error searching {source}: {result}")
            else:
                all_jobs.extend(result)
        
        return {
            "total": len(all_jobs),
            "jobs": all_jobs,
            "sources_searched": active_sources,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def search_by_location(
        self,
        location: str,
        sources: List[str],
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Search for jobs by location"""
        if filters is None:
            filters = {}
        
        filters["location"] = location
        return await self.search(f"jobs in {location}", sources, filters)
    
    async def search_by_role(
        self,
        role: str,
        location: str,
        sources: List[str],
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Search for jobs by role and location"""
        if filters is None:
            filters = {}
        
        filters["location"] = location
        query = f"{role} in {location}"
        return await self.search(query, sources, filters)


job_search_service = JobSearchService()
