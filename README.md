# ACEest Fitness & Gym — DevOps CI/CD Project

> **Course:** Introduction to DevOps (CSIZG514 / SEZG514 / SEUSZG514) — S2-25  
> **Assignment 1:** Automated CI/CD Pipelines  

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Application Architecture](#application-architecture)
3. [Repository Structure](#repository-structure)
4. [Local Setup & Execution](#local-setup--execution)
5. [Running Tests Manually](#running-tests-manually)
6. [Docker Usage](#docker-usage)
7. [GitHub Actions — CI/CD Pipeline](#github-actions--cicd-pipeline)
8. [Jenkins BUILD Integration](#jenkins-build-integration)
9. [API Reference](#api-reference)
10. [Version History](#version-history)

---

## Project Overview

ACEest Fitness & Gym is a **Flask REST API** that manages gym clients, fitness programs, workout tracking, and membership status. This project demonstrates a complete DevOps lifecycle:

```
Local Dev → Git Push → GitHub Actions (Lint → Test → Docker Build) → Jenkins BUILD
```

---

## Application Architecture

```
aceest_project/
├── app.py                    # Flask REST API (core application)
├── requirements.txt          # Python dependencies
├── Dockerfile                # Multi-stage Docker image
├── Jenkinsfile               # Jenkins declarative pipeline
├── .github/
│   └── workflows/
│       └── main.yml          # GitHub Actions CI/CD workflow
├── tests/
│   └── test_app.py           # Pytest unit test suite (40+ tests)
└── README.md
```

**Tech Stack:**

| Layer       | Technology              |
|-------------|-------------------------|
| Language    | Python 3.12             |
| Web Framework | Flask 3.x             |
| Database    | SQLite (via sqlite3)    |
| Testing     | Pytest + pytest-cov     |
| Container   | Docker (multi-stage)    |
| CI/CD       | GitHub Actions          |
| Build Server | Jenkins                |

---

## Repository Structure

```
.
├── app.py               ← Main Flask application
├── requirements.txt     ← pip dependencies
├── Dockerfile           ← Multi-stage Docker build
├── Jenkinsfile          ← Jenkins pipeline definition
├── README.md
├── .github/
│   └── workflows/
│       └── main.yml     ← GitHub Actions pipeline (3 jobs)
└── tests/
    └── test_app.py      ← 40+ Pytest unit & integration tests
```

---

## Local Setup & Execution

### Prerequisites

- Python 3.10+
- pip
- (Optional) Docker Desktop

### Step-by-Step

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/aceest-devops.git
cd aceest-devops

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialise the database and start the server
python app.py
```

The API will be available at: **http://localhost:5000**

Verify it's running:
```bash
curl http://localhost:5000/health
# → {"status": "healthy", "app": "ACEest Fitness & Gym"}
```

---

## Running Tests Manually

```bash
# Activate venv first (see above), then:

# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=app --cov-report=term-missing

# Run a specific test class
pytest tests/test_app.py::TestClientCreate -v

# Run a single test
pytest tests/test_app.py::TestCalculateCalories::test_fat_loss_factor -v
```

Expected output:
```
tests/test_app.py::TestHealthCheck::test_health_returns_200           PASSED
tests/test_app.py::TestCalculateCalories::test_fat_loss_factor        PASSED
...
============= 40+ passed in X.XXs =============
```

**Test Coverage Areas:**

| Module              | Tests |
|---------------------|-------|
| Health check        | 2     |
| Business logic      | 10    |
| Authentication      | 5     |
| Client CRUD         | 13    |
| Programs endpoints  | 4     |
| Progress tracking   | 6     |
| Workout logging     | 3     |
| Membership check    | 2     |

---

## Docker Usage

### Build the image

```bash
docker build -t aceest-fitness:latest .
```

### Run the container

```bash
docker run -d \
  --name aceest \
  -p 5000:5000 \
  -v aceest_data:/app/data \
  aceest-fitness:latest
```

### Verify

```bash
curl http://localhost:5000/health
```

### Stop and remove

```bash
docker stop aceest && docker rm aceest
```

**Dockerfile Design Decisions:**
- **Multi-stage build** — separates dependency installation from the runtime image, keeping the final image small.
- **Non-root user** — runs as `aceest` (not root) for security.
- **Named volume** — persists the SQLite database across container restarts.

---

## GitHub Actions — CI/CD Pipeline

File: `.github/workflows/main.yml`

**Triggers:** Every `push` to `main`/`develop` and every `pull_request` targeting `main`.

### Pipeline Jobs (run in sequence)

```
[lint] → [test] → [docker]
```

| Job | Steps | Purpose |
|-----|-------|---------|
| **lint** | flake8 | Syntax & style check — fails build on critical errors |
| **test** | pytest + coverage | Validates all business logic before Docker build |
| **docker** | docker build + health check | Proves container builds and starts correctly |

**Viewing pipeline results:**  
Go to your repo on GitHub → **Actions** tab → select the latest workflow run.

---

## Jenkins BUILD Integration

File: `Jenkinsfile`

### Setup (one-time)

1. **Install Jenkins** (localhost or server):
   ```bash
   docker run -d -p 8080:8080 -v jenkins_home:/var/jenkins_home jenkins/jenkins:lts
   ```

2. **Required Jenkins Plugins:**
   - Git Plugin
   - Pipeline Plugin
   - HTML Publisher Plugin
   - Docker Pipeline Plugin

3. **Create a new Pipeline job:**
   - Jenkins Dashboard → **New Item** → **Pipeline**
   - Under *Pipeline*, select **Pipeline script from SCM**
   - SCM: `Git`, Repository URL: `https://github.com/<you>/aceest-devops.git`
   - Script Path: `Jenkinsfile`

4. **Configure GitHub Webhook** (for automatic triggers):
   - GitHub repo → **Settings → Webhooks → Add webhook**
   - Payload URL: `http://<jenkins-host>:8080/github-webhook/`
   - Content type: `application/json`
   - Events: `Just the push event`

### Jenkins Pipeline Stages

```
Checkout → Environment Setup → Lint → Unit Tests → Docker Build → Container Smoke Test
```

| Stage | Action |
|-------|--------|
| **Checkout** | Pulls latest code from GitHub |
| **Environment Setup** | Creates venv, installs requirements |
| **Lint** | Runs flake8 on app.py |
| **Unit Tests** | Runs pytest, generates JUnit XML + coverage report |
| **Docker Build** | Builds image tagged with build number |
| **Container Smoke Test** | Starts container, hits `/health`, tears down |

### Viewing Results

- **Test Results:** Jenkins job → **Test Result** (JUnit report)
- **Build Console:** Jenkins job → **Console Output**
- **Coverage Report:** Jenkins job → **Coverage Report** (HTML)

---

## API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login` | Login with `{"username":"admin","password":"admin123"}` |
| POST | `/api/logout` | Clear session |

### Clients

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/clients` | List all clients |
| POST | `/api/clients` | Create client |
| GET | `/api/clients/<name>` | Get client by name |
| PUT | `/api/clients/<name>` | Update client |
| DELETE | `/api/clients/<name>` | Delete client |

### Programs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/programs` | List program names |
| GET | `/api/programs/<name>` | Get program details |

Available programs: `Fat Loss`, `Muscle Gain`, `Beginner`

### Progress & Workouts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/clients/<name>/progress` | Get weekly adherence history |
| POST | `/api/clients/<name>/progress` | Log adherence `{"adherence": 85}` |
| GET | `/api/clients/<name>/workouts` | Get workout log |
| POST | `/api/clients/<name>/workouts` | Log workout `{"workout_type":"Strength","duration_min":60}` |
| GET | `/api/clients/<name>/membership` | Check membership status |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check — returns `{"status":"healthy"}` |

---

## Version History

| Version | Changes |
|---------|---------|
| 1.0 | Initial Tkinter UI — program display only |
| 1.1 | Added client profile form, progress slider |
| 2.0 | Added SQLite persistence, save/load client |
| 2.1 | Added weekly progress logging |
| 2.2 | Added matplotlib progress chart |
| 2.2.4 | Added CSV export, multi-client table |
| 3.0.1 | Added role-based login screen |
| 3.1.2 | Added workout & exercise tracking |
| **3.2.4** | Full feature Tkinter version (AI program gen, PDF report) |
| **Flask** | **This project** — rewritten as Flask REST API with full CI/CD |

---

*Submitted for Introduction to DevOps (CSIZG514) — BITS Pilani, S2-2025*
 
# aceest-devops-bits
