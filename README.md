# Job Market Intelligence Platform

An end-to-end Data Engineering project that ingests US job listings from the Adzuna API, stores raw data in PostgreSQL, transforms it into a dimensional data warehouse, and exposes analytics-ready datasets for labor market intelligence.

**Core business question:** *What does the current US job market look like for data professionals, and which opportunities are realistically accessible to remote-first candidates?*

---

## Data Engineering Highlights

* Built an end-to-end ETL pipeline using Python and SQLAlchemy.
* Automated ingestion of job market data from the Adzuna REST API.
* Designed and implemented a dimensional data warehouse using a Star Schema.
* Created fact and dimension tables with surrogate keys.
* Applied data transformation and normalization processes during ingestion.
* Implemented duplicate detection and data quality controls.
* Structured the project using layered architecture (Raw → Warehouse → Analytics).
* Prepared analytics-ready datasets for dashboards, reporting, and exploratory analysis.

---

## Key Findings

| Area                                 | Finding                                       |
| ------------------------------------ | --------------------------------------------- |
| **Top skills to prioritize**         | SQL, Machine Learning, GCP                    |
| **Expected remote salary**           | ~$93,000 USD / year                           |
| **Remote share of market**           | ~20% of total US listings                     |
| **Best roles for remote applicants** | Data Engineer, Data Analyst, Business Analyst |

> **Note on remote data:** Job postings that do not specify an explicit location are classified as remote in the source data, which may inflate this figure slightly. The ~20% estimate should be interpreted as an upper bound.

---

## What This Project Covers

* **Skill demand analysis** - Most requested tools and technologies by role.
* **Salary benchmarking** - Compensation ranges by title, seniority, and work arrangement.
* **Remote opportunity mapping** - Share of remote roles by title and location.
* **Hiring trends analysis** - Companies and job categories with the highest demand.
* **Role targeting for international applicants** - Identifying which roles have the highest density of remote opportunities.
* **Dimensional modeling** - Building analytics-ready structures for business intelligence workloads.

---

## Architecture

```text
Adzuna API
    │
    ▼
Raw Layer (job_listings)
    │
    ▼
Transformation Layer
    │
    ▼
Data Warehouse
    ├── dim_company
    ├── dim_job
    ├── dim_location
    ├── dim_date
    └── fact_job_listing
    │
    ▼
Analytics Layer
    ├── SQL Views
    ├── Dashboards
    └── Business Intelligence
```

---

## Data Warehouse Design

### Fact Table

| Table            | Grain                                                |
| ---------------- | ---------------------------------------------------- |
| fact_job_listing | One row per unique job posting collected from Adzuna |

### Dimensions

| Dimension    | Purpose                            |
| ------------ | ---------------------------------- |
| dim_company  | Hiring companies                   |
| dim_job      | Job attributes and classifications |
| dim_location | Geographic information             |
| dim_date     | Time-based analysis                |

The warehouse follows a Star Schema design optimized for analytical workloads and business intelligence reporting.

---

## Technology Stack

| Layer           | Technology                              |
| --------------- | --------------------------------------- |
| Ingestion       | Python · Adzuna REST API                |
| Data Modeling   | SQLAlchemy ORM                          |
| Storage         | PostgreSQL                              |
| Data Warehouse  | Star Schema · Fact & Dimension Modeling |
| Processing      | Pandas                                  |
| Analytics       | SQL · Jupyter                           |
| Infrastructure  | Docker                                  |
| Version Control | Git · GitHub                            |

---

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/FrancoFM93/job-market-intelligence-platform.git
cd job-market-intelligence-platform
pip install -r requirements.txt
```

### 2. Configure credentials

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Adzuna API Credentials
ADZUNA_APP_ID=your_app_id_here
ADZUNA_APP_KEY=your_app_key_here

# PostgreSQL Database
DB_HOST=localhost
DB_PORT=5433
DB_NAME=jobmarket
DB_USER=jobmarket
DB_PASSWORD=jobmarket
```

### 3. Provision the database

Make sure PostgreSQL is running and create the required database:

```sql
CREATE USER jobmarket WITH PASSWORD 'your_password';
CREATE DATABASE jobmarket OWNER jobmarket;
GRANT ALL PRIVILEGES ON DATABASE jobmarket TO jobmarket;
```

### 4. Run the ingestion pipeline

```bash
python pipeline.py
```

The pipeline will:

* Create the database schema if it does not exist.
* Fetch job listings from the Adzuna API.
* Transform and normalize raw records.
* Populate the warehouse dimensions and fact tables.
* Skip duplicate records automatically.

### 5. Explore the data

```bash
jupyter lab notebooks/
```

---

## Project Structure

```text
job-market-intelligence-platform/
├── db/
│   ├── connection.py
│   ├── models.py
│   └── __init__.py
│
├── ingestion/
│   ├── api_client.py
│   └── __init__.py
│
├── processing/
│   ├── transform.py
│   └── __init__.py
│
├── warehouse/
│   ├── warehouse_models.py
│   ├── fact_models.py
│   ├── load_dim_company.py
│   ├── load_dim_job.py
│   ├── load_dim_location.py
│   ├── load_dim_date.py
│   └── load_fact_job_listing.py
│
├── notebooks/
│   └── 01_eda.ipynb
│
├── tests/
│
├── pipeline.py
├── docker-compose.yml
├── requirements.txt
├── GUIDE.md
└── .env
```

---

## Reproducing the Analysis

The pipeline currently targets the following job families:

* Data Analyst
* Data Scientist
* Data Engineer
* Business Analyst
* Analytics Engineer
* Machine Learning Engineer

To reproduce the analysis:

1. Complete the setup steps above.
2. Run:

```bash
python pipeline.py
```

3. Open the notebooks and execute all cells.

Data freshness depends on when the pipeline was last executed. Re-running the pipeline pulls the latest available listings from the source API.

---

## Future Improvements

* Work arrangement dimension (Remote / Hybrid / On-site).
* Analytics views and semantic layer.
* Dashboard implementation with Streamlit or Power BI.
* Orchestration with Apache Airflow.
* Cloud deployment on AWS.
* CI/CD pipeline with GitHub Actions.
* Automated data quality testing.

---

## Notes for International Applicants

This project was originally built with a specific lens: identifying remote-first opportunities in the US market that may be accessible to candidates based outside the country.

Key observations from the current dataset:

* Remote roles represent roughly **20% of total listings**.
* **Data Engineer**, **Data Analyst**, and **Business Analyst** roles currently show the strongest remote presence.
* Average remote compensation is approximately **$93,000 USD per year**.
* The strongest recurring skill signals are **SQL**, **Machine Learning**, and **Google Cloud Platform (GCP)**.

---

## License

MIT
