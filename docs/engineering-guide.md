# Engineering Guide

This document describes the development workflow, project structure, and common commands used throughout the repository.

For architectural decisions and implementation rationale, see the Engineering Walkthrough.

---

# Repository Structure

```text
job-market-intelligence-platform/

├── analytics/          # Analytical SQL queries and reporting
├── config/             # Configuration management
├── db/                 # Operational database models and connection
├── docs/               # Engineering documentation
├── ingestion/          # API clients
├── notebooks/          # Exploratory analysis
├── processing/         # Validation and transformation logic
├── tests/              # Automated tests
├── warehouse/          # Warehouse models and builders

pipeline.py             # Main ingestion pipeline
logger.py               # Logging configuration
```

---

# Development Environment

## Create a virtual environment

```bash
python -m venv venv
```

Windows

```bash
venv\Scripts\activate
```

Linux / macOS

```bash
source venv/bin/activate
```

---

## Install dependencies

Runtime

```bash
pip install -r requirements.txt
```

Development

```bash
pip install -r requirements-dev.txt
```

---

# Configuration

The project uses environment variables for configuration.

Create a `.env` file using `.env.example`.

Required variables:

```text
ADZUNA_APP_ID
ADZUNA_APP_KEY

DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
```

---

# Docker

Start PostgreSQL

```bash
docker compose up -d
```

Stop PostgreSQL

```bash
docker compose down
```

---

# Running the Pipeline

Execute:

```bash
py pipeline.py
```

Current ingestion flow:

```text
Fetch

↓

Validate

↓

Transform

↓

Persist
```

The pipeline reports:

- Inserted records
- Skipped records
- Rejected records
- Errors

Validation failures are logged without interrupting the ingestion process.

---

# Warehouse

Build the dimensional warehouse separately.

```bash
py -m warehouse.build_warehouse
```

The warehouse process is intentionally decoupled from ingestion.

---

# Testing

Run the complete test suite.

```bash
py -m pytest -q -p no:cacheprovider
```

The repository currently includes tests for:

- API client
- Validation
- Transformations
- Pipeline behavior
- Database models

---

# Logging

Logs are written through the centralized logging configuration.

Validation failures generate warnings.

Unexpected exceptions generate error logs.

Pipeline execution finishes with a summary containing:

- Inserted
- Skipped
- Rejected
- Errors

---

# Development Workflow

Recommended workflow for new features:

```text
Design

↓

Implementation

↓

Unit Tests

↓

Integration

↓

Documentation

↓

Git Review

↓

Commit

↓

Pull Request
```

Documentation should be updated together with the corresponding code changes.

---

# Coding Principles

The project follows a few guiding principles:

- Keep modules focused on a single responsibility.
- Validate data before transformation.
- Prefer explicit behavior over implicit assumptions.
- Keep business rules separate from persistence.
- Write tests for new functionality.
- Keep documentation synchronized with implementation.

---

# Documentation

The repository documentation is organized as follows.

| Document | Purpose |
|-----------|---------|
| README | Project overview |
| Engineering Guide | Development reference |
| Engineering Walkthrough | Architecture and design decisions |
| Architecture Decision Records | Long-term technical decisions |

---

# Branch Strategy

Feature development should occur in dedicated branches.

Example:

```text
feature/data-validation
feature/testing-layer
feature/data-warehouse
```

Merge into `main` only after:

- Tests pass
- Documentation is updated
- Code review is complete