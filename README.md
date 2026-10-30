# Job Application Automation Assistant

A Python-based local web application that helps fresh graduates discover relevant jobs in the Philippines and remote positions, evaluate job compatibility, prepare applications, and track applications from a single dashboard.

The application is designed around **human-in-the-loop job applications**.

The system can automatically discover jobs, filter them, score them against the user's resume, generate application answers, and use browser automation to fill application forms. The user reviews the completed application and manually submits it.

## Current Build Status

Working end-to-end, including a browser-based single-page dashboard:

- ✅ Profile creation/selection, resume upload (PDF/DOCX) + extraction + verification
- ✅ Configurable search settings (salary, remote, fresh-grad, excluded categories, sources)
- ✅ Job discovery through Indeed/JobStreet/Kalibrr connectors with deterministic filtering
- ✅ Deterministic job matching (title / skills / experience / location / salary / fresh-grad)
- ✅ Application lifecycle: create → generate answers → prepare → submit → track (incl. events)
- ✅ AI via **OpenRouter with free models** (`google/gemma-4-31b-it:free` default).
  Without a key it falls back to truthful offline answers, so the app works 100% free.
- ⏳ Real (non-mock) job scraping and company career-page discovery are the next phase.

**API keys:** only a free OpenRouter key is needed for optional AI features.
Full free-key instructions live in `API_KEYS.md` (git-ignored). Copy `.env.example` to `.env`
and add the key there if you want AI answers instead of the local fallback.

**Run:** `python -m app` → http://localhost:8000

## Project Goal

Build a portfolio-quality job search assistant capable of:

- Searching multiple job boards
- Discovering openings from company career pages
- Supporting Philippine-based jobs
- Supporting legitimate remote/work-from-home jobs open to applicants in the Philippines
- Parsing a user's resume
- Creating a structured candidate profile
- Matching jobs against the candidate's qualifications
- Filtering out unsuitable jobs
- Generating personalized application answers
- Preparing applications through browser automation
- Tracking applications
- Preventing accidental duplicate applications
- Supporting manual re-application when explicitly requested
- Providing a dashboard showing the entire job-search pipeline

## Core Principles

### 1. Human-in-the-loop

The application must NOT automatically submit job applications.

The automation should stop before the final submission step.

Example:

```text
Open application
      ↓
Fill personal information
      ↓
Fill education
      ↓
Fill experience
      ↓
Upload resume
      ↓
Answer application questions
      ↓
Pause
      ↓
User reviews application
      ↓
User clicks Submit manually
```

### 2. Accuracy over quantity

The system should prioritize relevant jobs instead of blindly applying to everything.

A job should receive a compatibility score based on:

- Required skills
- Preferred skills
- Education
- Experience requirements
- Job title
- Location
- Remote eligibility
- Salary
- Employment type
- Fresh-graduate eligibility
- Technology stack

### 3. Never invent candidate information

The AI must never fabricate:

- Work experience
- Job experience
- Certifications
- Education
- Skills
- Employers
- Projects
- Salary history
- Professional achievements

If information is missing, the system should flag the question for manual input.

## Default Candidate Filters

The application should support configurable filters.

Default filters:

```text
Country: Philippines
Remote: Allowed
Fresh graduate: Allowed
Experience: 0–1 years preferred
Minimum salary: PHP 25,000/month
Daily application target: 50
```

The user must be able to change these settings from the dashboard.

## Excluded Job Categories

The default configuration should exclude:

- BPO
- Call Center
- Customer Service
- Sales
- Marketing
- Network Technician

Network-related jobs may be allowed if the actual position is primarily software development.

The excluded categories must be configurable rather than hard-coded.

## Supported Job Sources

The application should use a connector architecture.

Potential connectors include:

- LinkedIn
- Indeed
- JobStreet Philippines
- Kalibrr
- Glassdoor
- Jora
- Foundit
- Company career pages
- Other supported job websites

Each source should have its own connector implementation.

Example:

```text
scrapers/
├── base.py
├── linkedin.py
├── indeed.py
├── jobstreet.py
├── kalibrr.py
├── glassdoor.py
├── jora.py
├── foundit.py
└── company_sites.py
```

The system must respect each website's terms, robots rules, authentication requirements, and anti-automation mechanisms.

CAPTCHAs and similar challenges must never be bypassed.

## Resume Processing

The user should be able to upload:

- PDF
- DOCX

The application extracts:

- Name
- Contact information
- Education
- Skills
- Projects
- Internship
- Certifications
- Languages
- Other relevant information

The extracted information should be displayed for user confirmation before being used for applications.

Store a normalized candidate profile in the database.

## AI Integration

The application should support OpenRouter-compatible models.

The user should be able to configure:

```env
OPENROUTER_API_KEY=
OPENROUTER_MODEL=
```

The model should be configurable rather than hard-coded.

The application should also be architected so another provider can be added later.

Potential providers:

- OpenRouter
- Ollama
- Other OpenAI-compatible APIs

## AI Responsibilities

The AI may:

- Analyze resumes
- Analyze job descriptions
- Calculate compatibility
- Explain matching reasons
- Identify missing requirements
- Generate application answers
- Generate personalized cover letters
- Personalize company outreach emails
- Extract structured information from job descriptions

The AI must not:

- Invent qualifications
- Invent experience
- Automatically submit applications
- Make decisions that contradict explicit user filters

## Job Matching

Each discovered job should receive a score.

Example:

```text
Job Match: 87%

Skills:             92%
Experience:         100%
Education:          100%
Location:           100%
Salary:              80%
Job title:            90%
Overall:             87%
```

The dashboard should explain why a job received its score.

## Application Queue

Jobs can have statuses:

```text
DISCOVERED
REVIEWING
MATCHED
REJECTED
QUEUED
PREPARING
READY_FOR_REVIEW
SUBMITTED
INTERVIEW
REJECTED_AFTER_APPLICATION
OFFER
WITHDRAWN
```

## Daily Application Target

Default:

```text
50 applications/day
```

This is a target rather than an automatic submission limit.

The user can configure:

```text
Daily target
Minimum match score
Maximum applications
Preferred locations
Minimum salary
Allowed experience
Remote preference
```

## Duplicate Prevention

The system should detect duplicates using:

- Job URL
- Job-board job ID
- Company + title + location
- Normalized job URL

A previously applied job should normally be marked:

```text
ALREADY_APPLIED
```

However, the user must have a manual:

```text
RE-APPLY
```

action.

Re-apply must require explicit user interaction.

## Application Automation

Playwright should be used to automate browser interaction where technically and legally appropriate.

The automation should:

1. Open the job/application page.
2. Detect application fields.
3. Map fields to the candidate profile.
4. Fill known fields.
5. Upload the selected resume.
6. Generate answers for supported questions.
7. Flag uncertain questions.
8. Stop before submission.
9. Display the application to the user.
10. Allow the user to review.
11. User manually submits.
12. User marks the application as submitted.

The application must never attempt to bypass:

- CAPTCHA
- MFA
- anti-bot challenges
- authentication protections
- security mechanisms

## Company Career Pages

The system should support company career-page discovery.

The user can maintain a company list:

```text
Company
Website
Career URL
Location
Industry
Priority
```

The system can periodically inspect supported career pages and identify new openings.

## Company Outreach

The application may collect publicly available company recruiting/contact information where appropriate.

It can generate personalized outreach emails.

Example workflow:

```text
Company discovered
       ↓
Career page checked
       ↓
No suitable opening found
       ↓
Public recruiting contact found
       ↓
AI generates personalized email
       ↓
User reviews
       ↓
User sends manually
```

Email sending should initially be manual.

## Dashboard

The dashboard should contain:

### Overview

```text
Jobs Found
Strong Matches
Applications Prepared
Applications Submitted
Interviews
Offers
Rejected
```

### Job Feed

Each job should display:

```text
Company
Position
Location
Salary
Remote status
Experience requirement
Match score
Job URL
Source
Date discovered
Application status
```

### Application Queue

Show jobs ready for browser automation.

### Application Tracker

Track the entire application lifecycle.

### Resume

Allow the user to upload and update their resume.

### Settings

Configure:

- Salary
- Locations
- Remote preference
- Job titles
- Excluded categories
- Skills
- Daily target
- AI provider
- AI model
- Browser settings

## Security

Never hard-code:

- API keys
- Passwords
- Session tokens
- Credentials

Use `.env`.

Provide:

```text
.env.example
```

The real `.env` must be included in `.gitignore`.

Sensitive browser sessions should not be committed to GitHub.

## Database

Use SQLite initially.

Recommended entities:

```text
UserProfile
Resume
Skill
Job
Company
JobSource
Application
ApplicationAnswer
ApplicationEvent
SearchRun
CompanyContact
AIRequest
Settings
```

## Future Features

Potential future additions:

- PostgreSQL
- React frontend
- ✅ Docker (Dockerfile + docker-compose)
- ✅ Cloud deployment (Oracle Cloud Always-Free VM / GitHub Actions)
- Email integration
- Gmail integration
- Interview tracking
- Calendar integration
- Analytics
- Resume versions
- Multiple candidate profiles
- Cover-letter templates
- Job recommendation engine
- Local AI through Ollama

## Portfolio Positioning

This project should be presented as:

> An AI-assisted job discovery and application management platform built with Python, FastAPI, Playwright, SQLite, and LLM APIs.

Important portfolio features to demonstrate:

- Web scraping/data extraction
- Browser automation
- AI integration
- Natural-language processing
- Database design
- REST APIs
- Authentication/session handling
- Job matching algorithms
- Background tasks
- Human-in-the-loop automation
- Dashboard development
- Testing

## Development Philosophy

Build the application incrementally.

Do NOT attempt to implement every job board immediately.

Recommended order:

1. Project foundation
2. Database
3. Resume parser
4. Job model
5. Job ingestion
6. Filtering
7. Matching
8. Dashboard
9. AI integration
10. Application preparation
11. Playwright automation
12. Application tracking
13. Additional job connectors
14. Company career-page discovery

Every feature should be tested before moving to the next major feature.