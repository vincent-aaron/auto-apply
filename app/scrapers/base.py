"""Base job scraper connector"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
import hashlib


class BaseJobConnector(ABC):
    """Base class for job scraper connectors"""
    
    def __init__(self, name: str):
        self.name = name
        self.source = name.lower()
    
    @abstractmethod
    async def search(self, query: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for jobs
        
        Args:
            query: Search query (job title, skills, etc.)
            filters: Filter options (location, remote, etc.)
        
        Returns:
            List of normalized job objects
        """
        pass
    
    def normalize_job(
        self,
        title: str,
        company: str,
        description: str,
        source_job_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Normalize job data to standard format
        
        Args:
            title: Job title
            company: Company name
            description: Job description
            source_job_id: Unique ID from source
            **kwargs: Additional fields
        
        Returns:
            Normalized job object
        """
        # Generate source hash for deduplication
        source_hash_input = f"{self.source}:{company}:{title}:{kwargs.get('location', 'remote')}"
        source_hash = hashlib.md5(source_hash_input.encode()).hexdigest()
        
        job = {
            "title": title,
            "company": company,
            "description": description,
            "requirements": kwargs.get("requirements", ""),
            "location": kwargs.get("location"),
            "is_remote": kwargs.get("is_remote", False),
            "salary_min": kwargs.get("salary_min"),
            "salary_max": kwargs.get("salary_max"),
            "salary_currency": kwargs.get("salary_currency", "PHP"),
            "employment_type": kwargs.get("employment_type"),
            "experience_level": kwargs.get("experience_level"),
            "source": self.source,
            "source_job_id": source_job_id,
            "source_url": kwargs.get("source_url"),
            "source_hash": source_hash,
            "discovered_at": datetime.utcnow()
        }
        
        return job
    
    async def close(self):
        """Close any resources (override if needed)"""
        pass
