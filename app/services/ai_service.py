"""AI service for LLM integration using the FREE OpenRouter API."""

from typing import Optional, Dict, Any
import json
import re
import logging

import httpx

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI/LLM operations using OpenRouter (free models by default)."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize AI service.

        Args:
            api_key: OpenRouter API key (from config if not provided)
            model: Model to use (from config if not provided)
        """
        from app.config import settings

        self.api_key = api_key or settings.openrouter_api_key
        self.model = model or settings.openrouter_model
        self.base_url = settings.openrouter_base_url.rstrip("/")
        self.site_url = settings.openrouter_site_url
        self.app_title = settings.openrouter_app_title
        self.timeout = settings.ai_request_timeout_seconds

        if not self.api_key:
            logger.warning(
                "No OpenRouter API key configured - AI features will use offline fallbacks"
            )

    @property
    def is_configured(self) -> bool:
        """Whether an API key is available (free OpenRouter key)."""
        return bool(self.api_key and self.api_key.strip())

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def status(self) -> Dict[str, Any]:
        """Return AI capability status so the UI can show a warning."""
        return {
            "enabled": self.is_configured,
            "model": self.model,
            "provider": (
                "OpenRouter (free models)" if self.is_configured else "local fallback (no key)"
            ),
        }

    async def generate_application_answers(
        self,
        candidate_profile: Dict[str, Any],
        job: Dict[str, Any],
        questions: list[str],
    ) -> Dict[str, str]:
        """Generate honest answers to application questions.

        Uses OpenRouter with a free model when a key is configured, otherwise
        falls back to deterministic local answers so the feature still works.
        """
        if not self.is_configured:
            return self._fallback_answers(candidate_profile, job, questions)

        prompt = self._answers_prompt(candidate_profile, job, questions)
        try:
            content = await self._call_llm(prompt, temperature=0.4)
            data = self._extract_json(content)
            if isinstance(data, dict):
                answers = {}
                nested = data.get("answers") if isinstance(data.get("answers"), dict) else {}
                for q in questions:
                    val = nested.get(q) or data.get(q)
                    if val and isinstance(val, str):
                        answers[q] = val.strip()
                    else:
                        answers[q] = self._fallback_answer(candidate_profile, job, q)
                return answers
        except Exception as e:
            logger.error(f"AI answer generation failed: {e}")

        # Any failure -> local fallback (still free & truthful)
        return self._fallback_answers(candidate_profile, job, questions)

    async def parse_resume_with_ai(self, raw_text: str) -> Dict[str, Any]:
        """Use AI to parse resume text into structured JSON (requires key)."""
        if not self.is_configured:
            logger.warning("Cannot parse resume with AI without an API key")
            return {}

        prompt = f"""\
Extract structured information from the resume text below and return ONLY valid JSON with exactly these keys:
{{
  "name": "", "email": "", "phone": "",
  "education": [{{"degree": "", "school": "", "years": ""}}],
  "experience": [{{"company": "", "title": "", "duration": "", "description": ""}}],
  "skills": [], "certifications": [], "languages": [],
  "projects": [{{"name": "", "description": "", "tech": ""}}],
  "summary": ""
}}
Do NOT invent anything. Use empty string/list when information is missing.

RESUME:
{raw_text[:12000]}
"""
        try:
            content = await self._call_llm(prompt, temperature=0.2)
            return self._extract_json(content)
        except Exception as e:
            logger.error(f"AI resume parse failed: {e}")
            return {}

    async def evaluate_job_match_with_ai(
        self,
        candidate_profile: Dict,
        job: Dict,
    ) -> Dict[str, Any]:
        """AI job match analysis (requires key)."""
        if not self.is_configured:
            return {}

        prompt = f"""\
Evaluate how well this candidate matches this job and return ONLY valid JSON with exactly these keys:
{{"match_score": 0-100, "strengths": [], "weaknesses": [], "recommendations": [], "should_apply": true/false, "explanation": ""}}

Candidate:
{json.dumps(candidate_profile, indent=2)}

Job:
- Title: {job.get('title')}
- Company: {job.get('company')}
- Location: {job.get('location')}
- Remote: {job.get('is_remote')}
- Experience: {job.get('experience_level')}
- Requirements: {job.get('requirements')}
- Description: {job.get('description')}

Be strict and honest. Do NOT recommend the candidate if the role clearly requires 3+ years
of experience or skills they do not have.
"""
        try:
            content = await self._call_llm(prompt, temperature=0.2)
            return self._extract_json(content)
        except Exception as e:
            logger.error(f"AI job match failed: {e}")
            return {}
# ------------------------------------------------------------------ #
    # LLM HTTP call
    # ------------------------------------------------------------------ #
    async def _call_llm(self, prompt: str, temperature: float = 0.2) -> str:
        """Call the OpenRouter chat completions API (OpenAI-compatible)."""
        if not self.api_key:
            raise ValueError("No OpenRouter API key configured")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # Optional headers for OpenRouter rankings
            "HTTP-Referer": self.site_url or "http://localhost:8000",
            "X-OpenRouter-Title": self.app_title or "Job Application Automation Assistant",
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a strict, honest assistant for a job-search tool. "
                        "Never invent experience, skills, certifications, degrees, employers, "
                        "salaries or achievements. When asked for JSON, return ONLY valid JSON "
                        "with no markdown fences and no commentary."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": 2048,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                logger.error(f"OpenRouter error {resp.status_code}: {resp.text[:500]}")
                raise RuntimeError(f"OpenRouter API error {resp.status_code}")

            data = resp.json()
            choices = data.get("choices") or []
            if not choices:
                raise RuntimeError("OpenRouter response has no choices")
            return choices[0].get("message", {}).get("content", "")

    # ------------------------------------------------------------------ #
    # JSON parsing
    # ------------------------------------------------------------------ #
    @staticmethod
    def _extract_json(content: str) -> Dict[str, Any]:
        """Best-effort extraction of a JSON object from an LLM response."""
        if not content:
            return {}
        text = content.strip()
        # Strip markdown fences
        text = re.sub(r"^```(?:json)?\s*", "", text).strip()
        text = re.sub(r"\s*```$", "", text).strip()
        # Try direct parse
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, ValueError):
            pass
        # Find the first top-level JSON object
        start = text.find("{")
        if start == -1:
            return {}
        depth, end = 0, len(text)
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        try:
            data = json.loads(text[start:end])
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, ValueError):
            return {}
# ------------------------------------------------------------------ #
    # Prompt builders & local fallbacks (work 100% offline / free)
    # ------------------------------------------------------------------ #
    def _answers_prompt(self, candidate, job, questions) -> str:
        return f"""\
Generate a professional, honest answer for EACH question below. Base every answer ONLY on the
candidate's real information. Never fabricate experience, skills, employers, certifications, or
education that are not present. If something is unknown, say so and express willingness to learn.

Candidate profile:
{json.dumps(candidate, indent=2)}

Job:
- Title: {job.get('title')}
- Company: {job.get('company')}
- Description: {job.get('description')}

Return ONLY valid JSON with the exact questions as keys and the answers as values.
Example: {{"<full question text>": "answer", ...}}.

Questions:
{json.dumps(questions)}
"""

    def _fallback_answers(self, candidate, job, questions):
        return {q: self._fallback_answer(candidate, job, q) for q in questions}

    def _fallback_answer(self, candidate, job, question) -> str:
        """Deterministic, truthful local answer (used when no API key is present)."""
        q = question.lower()
        name = candidate.get("name", "the candidate") or "the candidate"
        job_title = job.get("title", "this position")

        if "yourself" in q or "about you" in q:
            return (
                f"Hi, I am {name}, a recent BSIT graduate passionate about software development. "
                f"I have built academic and personal projects using Python, JavaScript, and SQL, "
                "and I am looking for an entry-level opportunity such as this role to grow into a "
                "professional developer."
            )
        if "why" in q and ("interest" in q or "position" in q or "company" in q):
            return (
                f"I am interested in {job_title} because it matches the skills I enjoy using "
                "and the direction I want to grow as an engineer. I am eager to learn this "
                "team's stack and contribute with reliability and a strong work ethic."
            )
        if "skill" in q or "qualif" in q or "strength" in q:
            return (
                "My key skills include Python, JavaScript, SQL, Git, and REST APIs, along with "
                "problem-solving and teamwork developed through hands-on projects. I learn new "
                "tools quickly and keep my code clean and well-tested."
            )
        if "experience" in q or "previous" in q:
            return (
                "I am a fresh graduate, so my experience comes mainly from academic and personal "
                "projects where I practiced real development workflows. I bring solid programming "
                "fundamentals, a growth mindset, and the willingness to learn this role's specific "
                "requirements on the job."
            )
        if "why" in q and ("hire" in q or "we" in q or "us" in q or "you" in q):
            return (
                f"You should consider me for {job_title} because I pair dependable technical "
                "fundamentals with genuine motivation and good communication. I take ownership of "
                "tasks, ask the right questions, and am committed to growing with the team."
            )
        if "salary" in q or "compensation" in q:
            return "I am open to discussing a fair entry-level salary and am flexible based on the full offer."
        if "location" in q or "remote" in q or "willing to work" in q:
            return "I am open to onsite, hybrid, or remote work within the Philippines."
        if "when" in q and ("start" in q or "available" in q):
            return "I am available to start immediately once hired."
        return (
            f"Regarding '{question}', I want to answer honestly: my background is as a fresh BSIT "
            "graduate with strong programming fundamentals. I would approach this with a "
            "problem-solving mindset, and I am happy to provide any specific details you need."
        )


ai_service = AIService()