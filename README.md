# Beacon Commercial Register API

A FastAPI-based API for managing commercial register data with SQLite database and Redis caching.

## Features

- FastAPI Framework
- SQLite Database with async support
- Redis Caching
- Comprehensive Testing
- CI/CD Ready

## Quick Start

### Prerequisites

- Python 3.8+
- Redis server
- Git

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd Beacon
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Setup

```bash
cp env.example .env
```

### 3. Start the Application

```bash
python main.py
```

### 4. Access

- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs

### 5. Available Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/v1/companies/{uid}` - Get company by UID
- `POST /api/v1/companies/search` - Search companies
- `POST /api/v1/import` - Import data
- `GET /api/v1/export` - Export data

## Development

### Database Setup

```bash
python manage_db.py
```

### Run Tests

```bash
python tests/run_tests.py
```

### Run Workers

```bash
python run_worker.py
```

## Testing

Tests run against a local server instance. Make sure your application is running on `http://localhost:8000` before running tests.

## Configuration

The application uses environment-specific configuration files in `app/configs/`:
- `development.py` - Development settings
- `testing.py` - Testing settings  
- `production.py` - Production settings

Environment variables can be set in a `.env` file or directly in your shell.