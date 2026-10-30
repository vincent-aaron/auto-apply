# Setup Instructions

## Prerequisites

- Python 3.10 or higher
- pip
- Git

## Installation

### 1. Clone or navigate to the project

```bash
cd job-auto-apply
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

On Windows:

```bash
venv\Scripts\activate
```

On macOS/Linux:

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Install Playwright browsers

```bash
playwright install
```

### 6. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key:

```
OPENROUTER_API_KEY=your-api-key-here
OPENROUTER_MODEL=meta-llama/llama-2-70b-chat
```

### 7. Initialize the database

```bash
python -m app.database.init
```

### 8. Run the application

```bash
python -m app
```

The application will be available at: `http://localhost:8000`

## Running Tests

```bash
pytest
```

## Running with auto-reload (development)

```bash
uvicorn app.main:app --reload --port 8000
```
