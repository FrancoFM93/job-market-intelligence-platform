# Job Market Intelligence Platform

An end-to-end data pipeline that ingests US job listings from the Adzuna API, stores them in PostgreSQL, and analyzes the market for data-focused roles with a particular emphasis on remote opportunities relevant to international applicants.

**Core business question:** *What does the current US job market look like for data professionals, and which opportunities are realistically accessible to remote-first candidates?*

---

## Key Findings

| Area | Finding |
|---|---|
| **Top skills to prioritize** | SQL, Machine Learning, GCP |
| **Expected remote salary** | ~$93,000 USD / year |
| **Remote share of market** | ~20% of total US listings |
| **Best roles for remote applicants** | Data Engineer, Data Analyst, Business Analyst |

> **Note on remote data:** Job postings that do not specify an explicit location are classified as remote in the source data, which may inflate this figure slightly. The ~20% estimate should be interpreted as an upper bound.

---

## What This Project Covers

- **Skill demand analysis** - most requested tools and technologies by role.
- **Salary benchmarking** - compensation ranges by title, seniority, and work arrangement.
- **Remote opportunity mapping** - share of remote roles by title and location.
- **Top hiring companies and industries**
- **Role targeting for international applicants** - identifying which roles have the highest density of fully remote postings.

---

## Architecture

```
Adzuna API
    │
    ▼
ingestion/api_client.py       ← Fetches paginated job listings
    │
    ▼
processing/transform.py       ← Parses and normalises raw API data
    │
    ▼
PostgreSQL (job_listings)     ← Persistent storage via SQLAlchemy
    │
    ▼
notebooks/                    ← Analysis and visualisation (Jupyter)
```

---

## Stack

| Layer | Technology |
|---|---|
| Ingestion | Python · Adzuna REST API |
| Storage | PostgreSQL 16 · SQLAlchemy ORM |
| Processing | Pandas · pg8000 |
| Analysis | Jupyter Lab · Matplotlib · Seaborn · Plotly |

---

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/your-username/job-market-intelligence-platform.git
cd job-market-intelligence-platform
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Adzuna API — https://developer.adzuna.com
ADZUNA_APP_ID=app_id
ADZUNA_APP_KEY=app_key

# PostgreSQL
DB_HOST=localhost
DB_PORT=5433 *You have to double check in your machine
DB_NAME=jobmarket
DB_USER=jobmarket
DB_PASSWORD=jobmarket
```

### 3. Provision the database

Make sure PostgreSQL is running, then create the user and database:

```sql
CREATE USER jobmarket WITH PASSWORD 'your_password';
CREATE DATABASE jobmarket OWNER jobmarket;
GRANT ALL PRIVILEGES ON DATABASE jobmarket TO jobmarket;
```

### 4. Run the ingestion pipeline

```bash
python pipeline.py
```

This will create the schema on first run, fetch listings from the Adzuna API, and load them into the database. Duplicate records are skipped automatically.

### 5. Open the analysis notebooks

```bash
jupyter lab notebooks/
```

---

## Project Structure

```
job-market-intelligence-platform/
├── db/
│   ├── connection.py       # SQLAlchemy engine, session, and init_db()
│   ├── models.py           # ORM models
│   └── __init__.py
├── ingestion/
│   ├── api_client.py       # Adzuna API client
│   └── __init__.py
├── processing/
│   ├── transform.py        # Data parsing and normalisation
│   └── __init__.py
├── notebooks/
│   └── 01_eda.ipynb        # Exploratory data analysis
├── app/                    # Application modules
├── config/                 # Configuration files
├── dashboard/              # Dashboard assets
├── tests/                  # Test suite
├── pipeline.py             # Main ingestion entry point
├── docker-compose.yml      # Optional: containerised Postgres
├── requirements.txt
├── GUIDE.md
└── .env                    # Local credentials (not committed)
```

---

## Reproducing the Analysis

The pipeline targets **Data Analyst**, **Data Scientist**, **Data Engineer**, and **Business Analyst** roles across the United States. To replicate:

1. Complete the setup steps above.
2. Run `python pipeline.py` - fetches up to 5 pages per role by default. Adjust with `run(max_pages_per_role=N)`.
3. Open the notebooks in order and execute all cells.

Data freshness depends on when the pipeline was last run. Re-run at any time to pull the latest listings.

---

## Notes for International Applicants

This project was built with a specific lens: identifying **remote-first** opportunities in the US market that are accessible to candidates based outside the country.

- Remote roles represent roughly **20% of total listings**, a meaningful but competitive segment.
- **Data Engineer, Data Analyst, and Business Analyst** roles have the highest share of fully remote postings among the titles analysed.
- Target salary for a fully remote position is approximately **$93,000 USD/year** based on current market data.
- Skills with the strongest signal across remote job descriptions: **SQL**, **Machine Learning**, and **GCP**.

---

## License

MIT
