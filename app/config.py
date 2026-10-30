"""Application configuration"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Database
    database_url: str = "sqlite:///./job_auto_apply.db"

    # OpenRouter AI (uses FREE models by default - see API_KEYS.md)
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "google/gemma-4-31b-it:free"
    # Or set OPENROUTER_MODEL to "openrouter/free" (auto-routes to a free model)
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: Optional[str] = None   # Optional: your site URL (for rankings)
    openrouter_app_title: Optional[str] = None  # Optional: your app name (for rankings)
    ai_request_timeout_seconds: int = 60

    # Application
    debug: bool = False
    secret_key: str = "your-secret-key-here-change-in-production"

    # Job Search Defaults
    daily_application_target: int = 50
    minimum_salary_php: int = 25000
    country: str = "Philippines"
    allow_remote: bool = True
    allow_fresh_graduate: bool = True

    # Browser Automation
    headless_browser: bool = True
    browser_timeout_seconds: int = 30

    # Job Sources
    enable_linkedin: bool = False
    enable_indeed: bool = True
    enable_jobstreet: bool = True
    enable_kalibrr: bool = True
    enable_glassdoor: bool = False
    enable_jora: bool = False
    enable_foundit: bool = False

    # Excluded Categories
    excluded_categories: str = "BPO,Call Center,Customer Service,Sales,Marketing,Network Technician"

    @property
    def excluded_categories_list(self) -> list[str]:
        """Return excluded categories as a list."""
        return [cat.strip() for cat in self.excluded_categories.split(",") if cat.strip()]

    @property
    def enabled_sources(self) -> list[str]:
        """Return list of enabled job sources."""
        sources = []
        if self.enable_linkedin:
            sources.append("linkedin")
        if self.enable_indeed:
            sources.append("indeed")
        if self.enable_jobstreet:
            sources.append("jobstreet")
        if self.enable_kalibrr:
            sources.append("kalibrr")
        if self.enable_glassdoor:
            sources.append("glassdoor")
        if self.enable_jora:
            sources.append("jora")
        if self.enable_foundit:
            sources.append("foundit")
        return sources

    @property
    def ai_enabled(self) -> bool:
        """Whether an OpenRouter API key is configured."""
        return bool(self.openrouter_api_key and self.openrouter_api_key.strip())


settings = Settings()