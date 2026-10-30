"""Deterministic job filtering service (per WORKFLOW.md sections 6-8)."""

from typing import Dict, Any, Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)

# Philippine cities/areas accepted in the location field
PH_CITIES = [
    "manila", "makati", "quezon city", "taguig", "pasig", "pasay", "mandaluyong",
    "baguio", "cebu", "davao", "iloilo", "bacolod", "cagayan de oro", "zamboanga",
    "laguna", "cavite", "bulacan", "pampanga", "rizal", "batangas",
    "negros", "bicol", "palawan", "carmona", "dasmarinas", "antipolo",
]

SENIOR_TAGS_KEYWORDS = ["senior", "lead", "principal", "manager", "director", "head of"]
EXPERIENCE_REQUIRED_KEYWORDS = ["5+ years", "4+ years", "3+ years", "8+ years", "10+ years"]


class JobFilteringService:
    """Applies deterministic filters and returns (is_filtered_out, reason)."""

    def filter_job(
        self,
        job: Dict[str, Any],
        excluded_categories: Optional[List[str]] = None,
        allow_remote: bool = True,
        country: str = "Philippines",
    ) -> Tuple[bool, str]:
        """
        Decide whether a job should be filtered out.

        Returns:
            (filtered_out: bool, reason: str)
        """
        text = " ".join(
            str(job.get(k, "")) for k in ("title", "description", "requirements")
        ).lower()
        title = str(job.get("title", "")).lower()
        location = str(job.get("location", "") or "").lower()
        is_remote = bool(job.get("is_remote", False))
        exp_level = str(job.get("experience_level", "") or "").lower()

        # 1. Excluded categories (BPO, Call Center, Sales, Marketing, etc.)
        for cat in excluded_categories or []:
            if cat.strip().lower() in text:
                return True, f"Excluded category: {cat.strip()}"

        # 2. Experience: reject senior/lead/manager roles and 3+ year requirements
        for kw in SENIOR_TAGS_KEYWORDS:
            if kw in title:
                return True, f"Senior/lead role detected: {title}"
        for kw in EXPERIENCE_REQUIRED_KEYWORDS:
            if kw in text:
                return True, f"Requires {kw} experience"
        if exp_level and any(k in exp_level for k in ("senior", "lead", "manager", "director")):
            return True, f"Experience level too high: {exp_level}"

        # 3. Location: accept remote + Philippines locations, else reject
        if is_remote or allow_remote is False:
            return False, ""
        if not location:
            return False, ""
        if any(city in location for city in PH_CITIES) or "philippines" in location:
            return False, ""
        last_part = location.split(",")[-1].strip()
        if last_part.lower() in ("ph", "phl", "philippines"):
            return False, ""
        return True, f"Location not eligible for {country or 'Philippines'} applicants: {location}"

    def filter_jobs_batch(
        self,
        jobs: List[Dict[str, Any]],
        excluded_categories: List[str],
        allow_remote: bool = True,
        country: str = "Philippines",
    ) -> Tuple[List[Dict[str, Any]], List[Tuple[Dict[str, Any], str]]]:
        """Filter a list of job dicts.

        Returns:
            (kept_jobs, removed) where removed is a list of (job, reason).
        """
        kept: List[Dict[str, Any]] = []
        removed: List[Tuple[Dict[str, Any], str]] = []
        for job in jobs:
            out, reason = self.filter_job(
                job,
                excluded_categories=excluded_categories,
                allow_remote=allow_remote,
                country=country,
            )
            if out:
                removed.append((job, reason))
            else:
                kept.append(job)
        return kept, removed


job_filtering_service = JobFilteringService()