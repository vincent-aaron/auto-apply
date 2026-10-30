"""Job matching service"""

from typing import Dict, List, Any, Optional
import json


class JobMatchingService:
    """Service for matching jobs to candidate profile"""
    
    def __init__(self):
        pass
    
    def calculate_compatibility_score(
        self,
        job: Dict[str, Any],
        candidate_profile: Dict[str, Any],
        candidate_skills: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate job compatibility score based on multiple factors
        
        Returns:
            {
                "score": 0-100,
                "decision": "match" | "partial_match" | "poor_match",
                "matching_skills": [...],
                "missing_skills": [...],
                "explanation": "..."
            }
        """
        score = 0
        factors = {}
        
        # 1. Title relevance (20 points max)
        title_score = self._score_title_relevance(job.get("title", ""), candidate_profile)
        score += title_score
        factors["title_relevance"] = title_score
        
        # 2. Skills match (30 points max)
        skills_score, matching_skills, missing_skills = self._score_skills_match(
            job, candidate_skills
        )
        score += skills_score
        factors["skills_match"] = skills_score
        
        # 3. Experience level (15 points max)
        exp_score = self._score_experience_level(job, candidate_profile)
        score += exp_score
        factors["experience_match"] = exp_score
        
        # 4. Location/Remote (15 points max)
        location_score = self._score_location(job, candidate_profile)
        score += location_score
        factors["location_match"] = location_score
        
        # 5. Salary (10 points max)
        salary_score = self._score_salary(job, candidate_profile)
        score += salary_score
        factors["salary_match"] = salary_score
        
        # 6. Fresh graduate compatibility (10 points max)
        grad_score = self._score_fresh_graduate(job, candidate_profile)
        score += grad_score
        factors["fresh_grad_match"] = grad_score
        
        # Determine decision
        if score >= 75:
            decision = "strong_match"
        elif score >= 60:
            decision = "match"
        elif score >= 40:
            decision = "partial_match"
        else:
            decision = "poor_match"
        
        return {
            "score": score,
            "decision": decision,
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "factors": factors,
            "explanation": self._generate_explanation(factors, score)
        }
    
    def _score_title_relevance(self, job_title: str, candidate_profile: Dict) -> float:
        """Score based on job title relevance"""
        relevant_titles = [
            "software developer", "software engineer", "developer",
            "backend developer", "frontend developer", "fullstack developer",
            "python developer", "java developer", "web developer",
            "junior developer", "entry-level", "graduate"
        ]
        
        job_title_lower = job_title.lower()
        
        if any(title in job_title_lower for title in relevant_titles):
            return 20
        elif any(word in job_title_lower for word in ["developer", "engineer", "programmer"]):
            return 15
        else:
            return 0
    
    def _score_skills_match(
        self,
        job: Dict,
        candidate_skills: List[str]
    ) -> tuple[float, List[str], List[str]]:
        """Score based on skill match"""
        score = 0
        matching = []
        missing = []
        
        # Extract required skills from job description
        # This is simplified; in production use AI
        required_skills = self._extract_job_skills(job)
        
        candidate_skills_lower = [s.lower() for s in candidate_skills]
        
        for skill in required_skills:
            if skill.lower() in candidate_skills_lower:
                matching.append(skill)
                score += 1.5  # 1.5 points per matching skill (max 30)
            else:
                missing.append(skill)
        
        # Cap at 30 points
        score = min(score, 30)
        
        return score, matching, missing
    
    def _extract_job_skills(self, job: Dict) -> List[str]:
        """Extract skills mentioned in job posting"""
        # Simplified skill extraction
        common_skills = [
            "Python", "Java", "JavaScript", "C++", "C#",
            "React", "Angular", "Vue", "Django", "FastAPI",
            "SQL", "MongoDB", "PostgreSQL",
            "Git", "Docker", "AWS", "Azure", "GCP",
            "REST API", "GraphQL", "Agile"
        ]
        
        skills = []
        text = f"{job.get('title', '')} {job.get('description', '')} {job.get('requirements', '')}".lower()
        
        for skill in common_skills:
            if skill.lower() in text:
                skills.append(skill)
        
        return skills
    
    def _score_experience_level(self, job: Dict, candidate_profile: Dict) -> float:
        """Score based on experience level requirement"""
        exp_level = job.get("experience_level", "").lower()
        candidate_exp = candidate_profile.get("years_experience", 0)
        
        # Fresh graduates can apply to entry-level and junior positions
        if any(level in exp_level for level in ["entry", "junior", "graduate", "intern"]):
            return 15
        elif "mid" in exp_level or "1-3" in exp_level:
            return 10
        elif "senior" in exp_level or "3+" in exp_level:
            return 0
        else:
            return 5
    
    def _score_location(self, job: Dict, candidate_profile: Dict) -> float:
        """Score based on location/remote preference"""
        is_remote = job.get("is_remote", False)
        
        # User preference to check - for now assume remote is okay
        if is_remote:
            return 15
        else:
            # Location-based scoring would go here
            return 10
    
    def _score_salary(self, job: Dict, candidate_profile: Dict) -> float:
        """Score based on salary"""
        min_salary = candidate_profile.get("minimum_salary", 25000)
        job_salary_min = job.get("salary_min")
        
        if not job_salary_min:
            return 5  # No salary info
        
        if job_salary_min >= min_salary:
            return 10
        else:
            return 5
    
    def _score_fresh_graduate(self, job: Dict, candidate_profile: Dict) -> float:
        """Score based on fresh graduate compatibility"""
        is_fresh = candidate_profile.get("is_fresh_graduate", True)
        
        if not is_fresh:
            return 5
        
        description = f"{job.get('description', '')} {job.get('requirements', '')}".lower()
        
        if any(phrase in description for phrase in ["fresh graduate", "no experience", "entry level"]):
            return 10
        elif any(phrase in description for phrase in ["graduate", "junior", "beginner"]):
            return 7
        else:
            return 3
    
    def _generate_explanation(self, factors: Dict, score: float) -> str:
        """Generate human-readable explanation of the score"""
        explanations = []
        
        if factors.get("title_relevance", 0) > 10:
            explanations.append("Strong title match")
        
        if factors.get("skills_match", 0) > 20:
            explanations.append("Good skills overlap")
        elif factors.get("skills_match", 0) > 10:
            explanations.append("Some skills match")
        
        if factors.get("experience_match", 0) >= 15:
            explanations.append("Perfect experience level")
        
        if factors.get("fresh_grad_match", 0) >= 10:
            explanations.append("Good for fresh graduates")
        
        if not explanations:
            explanations.append("Average match")
        
        return " • ".join(explanations)


job_matching_service = JobMatchingService()
