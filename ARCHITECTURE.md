"""Architecture documentation"""

# Job Application Automation Assistant - Architecture

## Overview

This is a layered, modular Python web application built with FastAPI for automating job discovery, matching, and application management.

## Directory Structure

```
job-auto-apply/
│
├── README.md                          # Project overview
├── WORKFLOW.md                        # User workflow documentation
├── ARCHITECTURE.md                    # This file
├── SETUP.md                          # Setup instructions
├── requirements.txt                   # Python dependencies
├── .env.example                      # Environment variables template
├── .gitignore                        # Git ignore rules
│
├── app/
│   ├── __init__.py                   # Package init
│   ├── __main__.py                   # Entry point for python -m app
│   ├── main.py                       # FastAPI app and routes setup
│   ├── config.py                     # Configuration from environment
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── base.py                   # SQLAlchemy base for models
│   │   └── database.py               # Database connection and session
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                   # UserProfile model
│   │   ├── resume.py                 # Resume model
│   │   ├── job.py                    # Job and Skill models
│   │   ├── application.py            # Application related models
│   │   ├── settings.py               # User settings model
│   │   └── search.py                 # SearchRun model
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py                   # User Pydantic schemas
│   │   ├── resume.py                 # Resume schemas
│   │   ├── job.py                    # Job schemas
│   │   ├── application.py            # Application schemas
│   │   └── settings.py               # Settings schemas
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── dashboard.py              # Dashboard routes
│   │   ├── users.py                  # User API routes
│   │   ├── jobs.py                   # Job API routes
│   │   ├── applications.py           # Application API routes
│   │   └── settings.py               # Settings API routes
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── resume_service.py         # Resume processing
│   │   ├── job_matching_service.py   # Job matching logic
│   │   └── ai_service.py             # LLM/AI integration
│   │
│   ├── scrapers/                     # Job scrapers (future)
│   │   ├── base.py
│   │   ├── indeed.py
│   │   ├── jobstreet.py
│   │   └── ...
│   │
│   ├── browser/                      # Browser automation (future)
│   │   ├── manager.py
│   │   ├── forms.py
│   │   └── profiles.py
│   │
│   ├── static/
│   │   ├── style.css                 # Main stylesheet
│   │   └── script.js                 # Frontend JavaScript
│   │
│   └── templates/                    # HTML templates (future)
│       ├── base.html
│       ├── dashboard.html
│       ├── profile.html
│       └── ...
│
├── tests/
│   ├── __init__.py
│   └── test_app.py                  # Application tests
│
└── data/
    └── .gitkeep
```

## Technology Stack

- **Framework**: FastAPI
- **ORM**: SQLAlchemy with SQLite
- **Validation**: Pydantic
- **Job Scraping**: BeautifulSoup, Playwright
- **Resume Processing**: PyPDF2, python-docx
- **AI Integration**: OpenRouter API
- **Browser Automation**: Playwright
- **Testing**: pytest
- **Task Scheduling**: APScheduler (for future background jobs)

## Database Models

### Core Entities

- **UserProfile**: Candidate profile with contact info
- **Resume**: Uploaded resume with extracted information
- **Skill**: Available skills (for matching)
- **Job**: Job listings from various sources
- **Application**: Job applications with status tracking
- **ApplicationAnswer**: Answers to application questions
- **ApplicationEvent**: Audit trail for applications
- **Settings**: User preferences and configuration
- **SearchRun**: Track individual search executions

## API Endpoints

### Dashboard

- `GET /` - Main dashboard page

### Users

- `POST /api/users/` - Create user profile
- `GET /api/users/{user_id}` - Get user profile
- `PUT /api/users/{user_id}` - Update user profile
- `GET /api/users/` - List all users

### Jobs

- `POST /api/jobs/` - Create job listing
- `GET /api/jobs/` - List jobs with filters
- `GET /api/jobs/{job_id}` - Get job details
- `PATCH /api/jobs/{job_id}` - Update job status

### Applications

- `POST /api/applications/` - Create application
- `GET /api/applications/{application_id}` - Get application
- `GET /api/applications/user/{user_id}` - List user applications
- `PATCH /api/applications/{application_id}` - Update application status

### Settings

- `GET /api/settings/{user_id}` - Get user settings
- `PUT /api/settings/{user_id}` - Update user settings

### Utility

- `GET /health` - Health check
- `GET /api/config` - Application configuration

## Service Layer

### ResumeService

Handles resume upload, file processing, and information extraction.

### JobMatchingService

Deterministic job matching with compatibility scoring based on:

- Title relevance (20 points)
- Skills overlap (30 points)
- Experience level (15 points)
- Location/Remote (15 points)
- Salary (10 points)
- Fresh graduate compatibility (10 points)

### AIService

LLM integration for:

- Intelligent resume parsing
- Application answer generation
- Advanced job matching

## Development Workflow

1. **Startup**: FastAPI initializes, database tables created
2. **User Setup**: User creates profile, uploads resume
3. **Configuration**: User configures search preferences
4. **Job Discovery**: Scrapers fetch jobs from multiple sources
5. **Deduplication**: Jobs checked for duplicates
6. **Filtering**: Jobs filtered by location, experience, salary, categories
7. **Matching**: Jobs scored against candidate profile
8. **Application**: User reviews and manually submits applications
9. **Tracking**: Application status updated in database

## Error Handling

- Validation errors return 400 Bad Request
- Not found errors return 404 Not Found
- Server errors return 500 Internal Server Error
- All errors include descriptive messages

## Configuration

Settings come from environment variables (`.env` file):

```
DATABASE_URL=sqlite:///./job_auto_apply.db
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=meta-llama/llama-2-70b-chat
DEBUG=False
DAILY_APPLICATION_TARGET=50
MINIMUM_SALARY_PHP=25000
```

## Security Considerations

- Never auto-submit applications (human-in-the-loop principle)
- Never bypass CAPTCHA or authentication
- API keys stored in environment, never in code
- Database file ignored in git
- Validate all user inputs

## Testing

Run tests with:

```bash
pytest tests/
```

## Next Phases

Phase 2: Resume Upload & Processing
Phase 3: Job Scrapers Implementation
Phase 4: Job Matching & Filtering
Phase 5: Application Answer Generation
Phase 6: Browser Automation
Phase 7: Dashboard UI Enhancement
Phase 8: Production Deployment
