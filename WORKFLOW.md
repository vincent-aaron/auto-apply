# Job Application Automation Workflow

## 1. Application Startup

```text
User opens local web application
        ↓
FastAPI starts
        ↓
Database initialized
        ↓
Configuration loaded
        ↓
Dashboard displayed
```

The application should run locally with a simple command such as:

```bash
python -m app
```

or:

```bash
uvicorn app.main:app --reload
```

## 2. Candidate Profile

The user uploads a resume.

Supported formats:

```text
PDF
DOCX
```

Processing:

```text
Resume
 ↓
Text extraction
 ↓
Section detection
 ↓
Structured candidate profile
 ↓
User verification
 ↓
Database
```

The user must verify the extracted information.

## 3. Search Configuration

The user configures:

```text
Target locations:
- Philippines
- Remote

Minimum salary:
PHP 25,000

Experience:
Fresh graduate / Entry level

Daily target:
50

Excluded categories:
BPO
Call Center
Customer Service
Sales
Marketing
Network Technician
```

The user can change these values.

## 4. Job Discovery

The system executes a search.

```text
Search scheduler
       ↓
Job source manager
       ↓
Individual connectors
       ↓
Raw job listings
```

Each connector should return a standardized job object.

Example:

```text
Job
├── title
├── company
├── location
├── remote
├── salary
├── description
├── requirements
├── URL
├── source
├── source_job_id
└── discovered_at
```

## 5. Deduplication

Before saving:

```text
Check URL
      ↓
Check source job ID
      ↓
Check company + title + location
      ↓
Duplicate?
 ├── YES → update existing job
 └── NO  → create job
```

## 6. Location Filtering

Accept:

```text
Philippines
Metro Manila
Bulacan
Pampanga
Other Philippine locations
Remote positions explicitly available to Philippine applicants
```

Reject:

```text
US only
Canada only
Australia only
UK only
Other locations where Philippine applicants are not eligible
```

The AI may assist with ambiguous location information, but the final filter must use deterministic rules where possible.

## 7. Experience Filtering

Preferred:

```text
Fresh graduate
Entry level
Junior
0 years
0–1 years
No experience required
```

Potentially acceptable:

```text
1–2 years
```

depending on the match score.

Strongly reject:

```text
3+ years required
5+ years required
Senior
Lead
Manager
Director
```

unless the user explicitly changes the configuration.

## 8. Role Filtering

The system should prioritize:

```text
Software Developer
Web Developer
Backend Developer
Frontend Developer
Full Stack Developer
Python Developer
PHP Developer
Java Developer
Junior Software Engineer
Software Engineer
AI Developer
AI Engineer
Application Developer
Programmer
IT Developer
```

The list must be configurable.

## 9. AI Job Matching

After deterministic filtering:

```text
Candidate profile
       +
Job description
       ↓
AI matcher
       ↓
Match score
       ↓
Explanation
```

Example:

```text
Match Score: 89%

Strong matches:
+ PHP
+ MySQL
+ JavaScript
+ Web development
+ Fresh graduate accepted

Weak matches:
- Laravel preferred
- 1 year experience preferred

Decision:
RECOMMENDED
```

## 10. Application Queue

Jobs should be sorted by:

```text
Match score
Salary
Location
Fresh graduate compatibility
Recency
User priority
```

Example:

```text
#1  94%  Junior Software Engineer
#2  91%  Web Developer
#3  89%  PHP Developer
#4  87%  AI Application Developer
```

## 11. Daily Application Target

The default target is:

```text
50 applications/day
```

The system should NOT automatically submit 50 applications.

Instead:

```text
50 recommended applications
        ↓
Application queue
        ↓
User chooses jobs
        ↓
Prepare application
        ↓
User reviews
        ↓
User manually submits
```

## 12. Application Preparation

User clicks:

```text
Prepare Application
```

Playwright opens the browser.

The system attempts to identify:

```text
First name
Last name
Email
Phone
Address
Education
School
Degree
Skills
Resume upload
Cover letter
Application questions
```

Known fields are automatically populated.

Unknown fields are flagged.

## 13. AI Application Questions

For example:

```text
Question:
Why are you interested in this position?
```

The AI receives:

```text
Candidate profile
Job description
Company information
```

and produces an answer.

The answer is shown to the user.

The user can:

```text
Accept
Edit
Regenerate
Reject
```

## 14. Truthfulness Guard

Before using an AI-generated answer:

```text
Generated answer
       ↓
Candidate fact validation
       ↓
Contains unsupported claim?
       ├── YES → FLAG
       └── NO  → APPROVED
```

Example:

The candidate has:

```text
Internship experience
```

The AI must NOT turn that into:

```text
2 years of professional experience
```

## 15. Human Review

The automation must stop before submission.

Dashboard:

```text
APPLICATION READY

Company:
Example Company

Position:
Junior Web Developer

Match:
91%

Resume:
resume_2026.pdf

Questions:
5 answered
1 requires review

[ Open Application ]
[ Review Answers ]
[ Cancel ]
```

## 16. Manual Submission

After reviewing:

```text
User opens browser
       ↓
Checks application
       ↓
User clicks Submit
       ↓
Application submitted
       ↓
User returns to dashboard
       ↓
Click "Mark as Submitted"
```

## 17. Application Tracking

After submission:

```text
SUBMITTED
    ↓
WAITING
    ↓
INTERVIEW
    ↓
OFFER
```

or:

```text
SUBMITTED
    ↓
REJECTED
```

The user can manually update statuses.

## 18. Duplicate Applications

When a user attempts to prepare an already-applied job:

```text
WARNING

You previously applied to:

Company: Example Company
Position: Junior Developer
Applied: August 10, 2026

[Cancel]
[Re-apply]
```

Re-apply is an explicit user action.

## 19. Company Career Search

The user can add companies.

Example:

```text
Company
Website
Career Page
Priority
```

The system checks supported career pages.

```text
Company career page
       ↓
Extract openings
       ↓
Normalize jobs
       ↓
Deduplicate
       ↓
Filter
       ↓
Match
       ↓
Dashboard
```

## 20. Company Outreach

If a suitable opening is not found:

```text
Company
 ↓
Public career/contact information
 ↓
AI personalized outreach draft
 ↓
User review
 ↓
User sends manually
```

The system should not mass-send unsolicited email automatically.

## 21. Scheduler

Example:

```text
08:00
Search jobs

12:00
Search new jobs

18:00
Search new jobs

22:00
Generate daily statistics
```

The user should be able to configure schedules.

## 22. Error Handling

Every connector must handle:

```text
Timeout
Page changed
HTTP error
Login required
CAPTCHA
Unavailable page
Missing field
Unexpected HTML
Rate limiting
```

CAPTCHA:

```text
STOP
 ↓
Notify user
 ↓
User handles challenge manually
```

Never attempt to bypass CAPTCHA.

## 23. Architecture

```text
                    ┌─────────────────┐
                    │    Dashboard    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    FastAPI      │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐    ┌───────▼──────┐    ┌───────▼───────┐
│ Job Discovery │    │ AI Matching  │    │ Applications  │
└───────┬───────┘    └───────┬──────┘    └───────┬───────┘
        │                    │                    │
┌───────▼────────────────────▼────────────────────▼───────┐
│                    Service Layer                         │
└──────────────────────────┬────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │       Database          │
              │         SQLite          │
              └─────────────────────────┘
```

## 24. Connector Architecture

All job sources should implement the same interface.

```text
BaseJobConnector
       │
       ├── LinkedInConnector
       ├── IndeedConnector
       ├── JobStreetConnector
       ├── KalibrrConnector
       ├── GlassdoorConnector
       ├── JoraConnector
       ├── FounditConnector
       └── CompanyCareerConnector
```

This allows additional sources to be added without rewriting the application.

## 25. Development Order

### Phase 1 — Foundation

```text
Project setup
FastAPI
SQLite
SQLAlchemy
Configuration
Logging
```

### Phase 2 — Resume

```text
PDF parser
DOCX parser
Candidate profile
Resume dashboard
```

### Phase 3 — Jobs

```text
Job model
Job ingestion
Deduplication
Filtering
Job dashboard
```

### Phase 4 — Matching

```text
Rule-based matching
AI matching
Match explanations
```

### Phase 5 — AI

```text
OpenRouter integration
Prompt management
Application answers
Cover letters
```

### Phase 6 — Browser Automation

```text
Playwright
Browser profiles
Form detection
Form filling
Resume upload
Review checkpoint
```

### Phase 7 — Tracking

```text
Application records
Status tracking
Re-apply
Statistics
```

### Phase 8 — More Sources

```text
Additional job boards
Company career pages
```

### Phase 9 — Portfolio Polish

```text
Authentication
Responsive UI
Error handling
Tests
Documentation
Screenshots
Docker
Deployment option
```

## Final User Experience

The finished application should feel like:

```text
                 JOBHUNT AI
────────────────────────────────────────

Jobs Found                 1,284
Strong Matches               146
Ready to Apply                72
Submitted                      31
Interviews                     4

────────────────────────────────────────

TOP MATCHES

91%  Junior Software Engineer
     Company A
     Makati / Hybrid
     ₱30,000–₱40,000

89%  Web Developer
     Company B
     Remote - Philippines
     ₱25,000+

87%  PHP Developer
     Company C
     Quezon City
     ₱28,000

        [Prepare Application]
────────────────────────────────────────
