# Job Market Intelligence Platform — Complete Guide

This document explains the full project from start to finish: what each piece does, why it was built that way, and how to talk about it confidently in an interview.

---

## Table of Contents

1. [What this project does (the big picture)](#1-what-this-project-does)
2. [Project structure](#2-project-structure)
3. [The tech stack and why each tool was chosen](#3-the-tech-stack)
4. [Step 1 — The database (PostgreSQL + Docker)](#4-step-1--the-database)
5. [Step 2 — Fetching data (Adzuna API)](#5-step-2--fetching-data)
6. [Step 3 — Storing data (SQLAlchemy models)](#6-step-3--storing-data)
7. [Step 4 — Transforming raw data](#7-step-4--transforming-raw-data)
8. [Step 5 — The pipeline](#8-step-5--the-pipeline)
9. [Step 6 — The analysis notebook](#9-step-6--the-analysis-notebook)
10. [Common interview questions and how to answer them](#10-interview-questions)

---

## 1. What this project does

This project automatically collects job listings for data roles (Data Analyst, Data Scientist, etc.) from a real job API, stores them in a database, and then analyzes them to answer questions like:

- What skills do companies actually ask for?
- How much do these jobs pay?
- How many positions are remote (relevant if you want to work internationally)?

The meta-narrative is powerful for interviews: **you used data skills to analyze the job market you are trying to enter.**

---

## 2. Project structure

```
job-market-intelligence-platform/
│
├── docker-compose.yml      # Starts the database with one command
├── pipeline.py             # The main script — runs the full data collection
├── requirements.txt        # Python libraries this project depends on
├── .env                    # Your secret credentials (API keys, DB password) — never commit this
├── .env.example            # A template showing what .env should look like (safe to share)
│
├── db/
│   ├── connection.py       # How to connect to the database
│   └── models.py           # The shape of the data (what columns the table has)
│
├── ingestion/
│   └── api_client.py       # Talks to the Adzuna API and fetches job listings
│
├── processing/
│   └── transform.py        # Converts raw API responses into structured data
│
└── notebooks/
    └── 01_eda.ipynb        # The analysis — charts, skills, salaries, remote jobs
```

---

## 3. The tech stack

| Tool | What it is | Why we use it |
|---|---|---|
| **Python** | Programming language | Industry standard for data work |
| **PostgreSQL** | Relational database | Stores job listings permanently and lets us query them with SQL |
| **Docker** | Runs PostgreSQL in an isolated container | No complex installation — one command starts the database on any machine |
| **SQLAlchemy** | Python library to interact with databases | Lets us define tables as Python classes and query without writing raw SQL |
| **pg8000** | PostgreSQL driver for Python | Connects Python to PostgreSQL; chosen because it's pure Python and avoids Windows encoding issues |
| **Adzuna API** | Job listings data source | Free API with real job postings across the US |
| **requests** | Python library for HTTP calls | Makes API calls simple |
| **python-dotenv** | Loads credentials from a `.env` file | Keeps secrets out of the code |
| **pandas** | Data manipulation library | The core tool for analysis — think of it as Excel for Python |
| **matplotlib / seaborn** | Charting libraries | Creates the visualizations |
| **Jupyter Notebook** | Interactive Python environment | Lets you run code step by step and see charts inline |

---

## 4. Step 1 — The database

**File:** `docker-compose.yml`

### What it does

This file tells Docker to start a PostgreSQL database. PostgreSQL is a professional relational database — the same kind used by real companies to store important data.

```yaml
services:
  db:
    image: postgres:15          # Use the official PostgreSQL version 15
    environment:
      POSTGRES_USER: jobmarket  # Create a user named "jobmarket"
      POSTGRES_PASSWORD: jobmarket
      POSTGRES_DB: jobmarket    # Create a database named "jobmarket"
    ports:
      - "5433:5432"             # Map port 5432 inside Docker to 5433 on your machine
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Persist data so it survives restarts
```

### Why Docker?

Installing PostgreSQL directly on Windows can be messy and conflict with other things (as you experienced — a local PostgreSQL was already installed). Docker wraps the database in a clean, isolated environment. You just run `docker-compose up -d` and the database exists. If something breaks, you can destroy and recreate it in seconds.

### The port mapping (5433:5432)

The format is `host_port:container_port`. PostgreSQL inside Docker listens on port 5432 (its default). We map it to 5433 on your machine because a local PostgreSQL installation was already occupying 5432. Think of it like an extension number — the database is "internally" on 5432 but you call it from outside on 5433.

### How to start/stop it

```bash
docker-compose up -d    # start in background (-d = detached)
docker-compose down     # stop and remove the container
docker-compose down -v  # stop AND delete all data (fresh start)
```

### Interview answer

> "I used Docker to run PostgreSQL so the setup is reproducible on any machine. It avoids environment conflicts and makes the project easy to demonstrate."

---

## 5. Step 2 — Fetching data

**File:** `ingestion/api_client.py`

### What it does

This file talks to the Adzuna API to download job listings. Adzuna is a job search engine that offers a free API for developers.

```python
BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search"

TARGET_ROLES = [
    "data analyst",
    "data scientist",
    "business analyst",
    "data engineer",
    "machine learning engineer",
    "analytics engineer",
]
```

We search for 6 different job titles, 5 pages each, 50 results per page. That gives us up to 1,500 job listings.

### The three functions

**`fetch_jobs(role, page)`** — Gets one page of results for one role.

It builds a URL like this:
```
https://api.adzuna.com/v1/api/jobs/us/search/1
  ?app_id=YOUR_ID
  &app_key=YOUR_KEY
  &results_per_page=50
  &what=data+analyst
```
The API responds with a JSON object containing a list of job listings.

**`fetch_all_jobs(role, max_pages)`** — Calls `fetch_jobs` in a loop for multiple pages, then combines all results. It also waits 0.5 seconds between pages (`time.sleep(0.5)`) to avoid overwhelming the API (this is called "rate limiting" — being polite to the server).

**`fetch_all_roles(max_pages_per_role)`** — Calls `fetch_all_jobs` for every role in `TARGET_ROLES` and tags each job with the search term that found it (stored as `search_role`).

### What is an API?

An API (Application Programming Interface) is a way for two programs to talk to each other over the internet. When you call the Adzuna API, you are sending an HTTP request (the same kind your browser sends when you visit a website), and Adzuna sends back data in JSON format.

JSON looks like this:
```json
{
  "results": [
    {
      "id": "12345",
      "title": "Data Analyst",
      "company": {"display_name": "Acme Corp"},
      "salary_min": 80000,
      "salary_max": 100000
    }
  ]
}
```

### Interview answer

> "I built an ingestion module that calls the Adzuna API for six different job titles, collecting up to 50 results per page across 5 pages. I added rate limiting between requests to respect the API's usage limits. Each job is tagged with the search query that returned it, which lets me analyze results by role later."

---

## 6. Step 3 — Storing data

**Files:** `db/models.py` and `db/connection.py`

### The model (`db/models.py`)

This file defines the shape of our data — what a job listing looks like when stored in the database. SQLAlchemy lets you define a database table as a Python class.

```python
class JobListing(Base):
    __tablename__ = "job_listings"

    id = Column(String, primary_key=True)   # Adzuna's unique ID for each job
    title = Column(String)                  # Job title
    company = Column(String)                # Company name
    location_display = Column(String)       # e.g. "Austin, Travis County"
    location_area = Column(String)          # State or metro area
    description = Column(Text)              # Full job description (long text)
    salary_min = Column(Float)              # Minimum salary if listed
    salary_max = Column(Float)              # Maximum salary if listed
    search_role = Column(String)            # Which query found this job
    created = Column(DateTime)              # When the job was posted
    fetched_at = Column(DateTime)           # When we downloaded it
    ...
```

Each `Column` becomes a column in the database table. This is called an **ORM (Object-Relational Mapper)** — it maps Python objects to database rows.

### The connection (`db/connection.py`)

This file sets up the connection to PostgreSQL using credentials from your `.env` file.

```python
load_dotenv()  # reads .env file into environment variables

DB_HOST = os.getenv("DB_HOST", "localhost")   # getenv reads the variable, "localhost" is the default
DB_PORT = os.getenv("DB_PORT", "5433")
...

DATABASE_URL = f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
```

The `DATABASE_URL` is a standard connection string format:
```
postgresql+pg8000://username:password@host:port/database_name
```

The `+pg8000` part tells SQLAlchemy which driver to use to actually talk to PostgreSQL. We use pg8000 instead of the more common psycopg2 because it's pure Python and avoids encoding issues on Windows with Spanish locale settings.

### Why `.env` files?

Your API key and database password are secrets. If you put them directly in the code and pushed to GitHub, anyone could see them. A `.env` file keeps them separate — it lives only on your machine and is listed in `.gitignore` so it never gets committed.

### Interview answer

> "I used SQLAlchemy's ORM to define the data model as a Python class. This means I never had to write `CREATE TABLE` SQL by hand — SQLAlchemy generates it. The database credentials are stored in a `.env` file, which is excluded from version control for security."

---

## 7. Step 4 — Transforming raw data

**File:** `processing/transform.py`

### What it does

The Adzuna API returns raw JSON with a specific structure. This file converts that raw JSON into a `JobListing` object that matches our database model.

```python
def parse_job(raw: dict) -> JobListing:
    location = raw.get("location", {})
    areas = location.get("area", [])
    # Adzuna returns area as a list: ["US", "Texas", "Austin"]
    # We take the last element (most specific: city or state)
    location_area = areas[-1] if areas else None

    return JobListing(
        id=raw.get("id"),
        title=raw.get("title"),
        company=raw.get("company", {}).get("display_name"),
        location_display=location.get("display_name"),
        location_area=location_area,
        ...
    )
```

This step is called **data transformation** — reshaping data from one format (API JSON) into another (our database structure). In data engineering, you often hear this referred to as part of the **ETL process**:

- **E**xtract — pull data from a source (the API call)
- **T**ransform — clean and reshape it (this file)
- **L**oad — store it in the destination (inserting into PostgreSQL)

### Interview answer

> "The transform layer decouples the API's data format from our storage format. If Adzuna changes their API response structure, I only need to update `transform.py` — the rest of the pipeline is unaffected."

---

## 8. Step 5 — The pipeline

**File:** `pipeline.py`

### What it does

This is the main script that runs everything in sequence. Think of it as the conductor of the orchestra.

```python
def run(max_pages_per_role: int = 5):
    # 1. Create the database table if it doesn't exist yet
    init_db()

    # 2. Fetch all jobs from the API
    raw_jobs = fetch_all_roles(max_pages_per_role=max_pages_per_role)

    # 3. Transform and load each job into the database
    session = SessionLocal()
    for raw in raw_jobs:
        job = parse_job(raw)
        if job.id is None:
            skipped += 1
            continue
        # Upsert: skip if this job ID already exists (avoids duplicates)
        exists = session.get(type(job), job.id)
        if exists:
            skipped += 1
            continue
        session.add(job)
    session.commit()
```

### Key concept: upsert / deduplication

Every job on Adzuna has a unique ID. Before inserting a job, we check if that ID already exists in the database. If it does, we skip it. This means you can run the pipeline multiple times without creating duplicate records. This pattern is called an **upsert** (update + insert).

### Key concept: session

A SQLAlchemy `session` is like a shopping cart. You add items to it (`session.add(job)`), and nothing actually goes to the database until you call `session.commit()`. If something goes wrong, `session.rollback()` throws everything away and nothing is saved. This protects your data from partial writes.

### Interview answer

> "The pipeline follows an ETL pattern. It initializes the schema, fetches from the API, transforms each record, and loads it with deduplication — if a job ID already exists in the database, we skip it. This makes the pipeline idempotent, meaning you can run it multiple times safely."

---

## 9. Step 6 — The analysis notebook

**File:** `notebooks/01_eda.ipynb`

EDA stands for **Exploratory Data Analysis** — the process of understanding a dataset by looking at it from different angles before drawing conclusions.

### Section 0: Setup

```python
import warnings
warnings.filterwarnings("ignore", ...)  # suppress internal library warnings
```
We suppress warnings from matplotlib's internals (they come from a library called pyparsing). They don't indicate any problem in our code — they're just noise from a version mismatch inside matplotlib.

```python
load_dotenv("../.env")  # reads credentials from the .env file one folder up
engine = create_engine(f"postgresql+pg8000://...")
with engine.connect() as conn:
    df = pd.read_sql("SELECT * FROM job_listings", conn)
```
We use `pd.read_sql()` with a SQLAlchemy engine (not a raw database connection) because that's what pandas officially supports. The result is a **DataFrame** — the core pandas data structure, essentially a table with rows and columns.

### Section 1: Dataset Overview

Basic counts and a bar chart showing listings per role. This gives you a first sanity check — does the data look right?

### Section 2: Skills Analysis

This is the most technically interesting part. We scan every job description with **regular expressions** (regex) to detect whether specific tools are mentioned.

```python
SKILLS = {
    'Python': r'\bpython\b',    # \b means "word boundary" — matches "python" but not "python3" inside a word
    'SQL':    r'\bsql\b',
    'Tableau': r'\btableau\b',
    ...
}

desc = df['description'].fillna('').str.lower()  # normalize to lowercase

for skill, pattern in SKILLS.items():
    matches = desc.str.contains(pattern, regex=True)  # True/False for each row
    skill_counts[skill] = matches.sum()               # count the Trues
```

We also build a heatmap showing which skills each role emphasizes. This is a `pandas` pivot (groupby) combined with seaborn's `heatmap`.

### Section 3: Salary Analysis

Not all jobs list a salary. For those that do, we:
1. Calculate the midpoint: `salary_mid = (salary_min + salary_max) / 2`
2. Filter out outliers: salaries below $20k or above $500k (likely data errors or hourly rates mislabeled)
3. Compare medians across roles with a box plot

A **box plot** shows the distribution of values: the box covers the middle 50% of data, the line in the middle is the median, and the whiskers extend to the typical range.

### Section 4: Location & Remote Analysis

We detect remote positions by searching for keywords across three fields: title, location, and description. Searching all three catches more cases than just checking one.

```python
remote_pattern = r'\bremote\b|\bwork\s+from\s+home\b|\bwfh\b|\bhybrid\b'

df['is_remote'] = (
    df['title'].fillna('').str.lower().str.contains(remote_pattern, regex=True) |
    df['location_display'].fillna('').str.lower().str.contains(remote_pattern, regex=True) |
    df['description'].fillna('').str.lower().str.contains(remote_pattern, regex=True)
)
```

The `|` operator here means "OR" — a job is flagged as remote if any of the three fields match.

We then break down remote availability by role, show which skills appear most in remote listings specifically, and compare salaries between remote, hybrid, and on-site positions.

---

## 10. Interview questions

### "Tell me about this project."

> "I built an end-to-end data pipeline that collects job listings from the Adzuna API, stores them in a PostgreSQL database, and analyzes them in a Jupyter notebook. The goal was to understand the US job market for data roles — what skills employers actually ask for, salary ranges by role, and how many positions are remote. I chose this project specifically because I wanted to apply data skills to a question that directly affects me: getting my first data job."

### "Why PostgreSQL instead of just a CSV file?"

> "A database lets me run the pipeline multiple times without creating duplicates — I check each job's ID before inserting. It also lets me query the data with SQL and scales better than a CSV if the dataset grows. And using a real database is closer to how production systems work."

### "What is Docker and why did you use it?"

> "Docker lets you run software in isolated containers. I used it to run PostgreSQL without installing it directly on my machine, which avoids version conflicts and makes the project easy to reproduce on any computer. You just run `docker-compose up` and the database is ready."

### "What is an ETL pipeline?"

> "ETL stands for Extract, Transform, Load. Extract means pulling data from a source — in this case, the Adzuna API. Transform means cleaning and reshaping it to fit our data model. Load means writing it to the destination, which is PostgreSQL. My `pipeline.py` orchestrates these three steps."

### "What is an ORM?"

> "ORM stands for Object-Relational Mapper. It's a library that lets you define database tables as Python classes and interact with them using Python instead of raw SQL. I used SQLAlchemy's ORM to define the `JobListing` model. When I call `init_db()`, SQLAlchemy reads that class and creates the table automatically."

### "How did you handle duplicates?"

> "Every job on Adzuna has a unique ID. Before inserting a record, I check if that ID already exists in the database. If it does, I skip it. This makes the pipeline idempotent — you can run it multiple times without corrupting the data."

### "How did you detect remote jobs?"

> "I used regular expressions to search for keywords like 'remote', 'work from home', 'WFH', and 'hybrid' across three fields: the job title, the location display name, and the full job description. Searching all three fields catches significantly more remote listings than just checking the location field."

### "What would you do to improve this project?"

> "A few things: First, run the pipeline on a schedule (daily or weekly) to capture market trends over time. Second, build an interactive dashboard with Plotly Dash or Streamlit so the analysis is easier to share. Third, use NLP to extract skills from descriptions more accurately — right now I'm using keyword matching, which misses synonyms and context."

---

*This guide was written to help you learn the project deeply, not just run it. Every concept here is something a real data professional uses daily.*
