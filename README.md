# Job Market Intelligence Platform

An end-to-end data pipeline that ingests US job listings from the Adzuna API and analyzes the market for Data Analyst and Data Scientist roles.

**Business question:** *What does the job market look like for aspiring data professionals in the US?*

## What it covers
- In-demand skills by role and location
- Salary ranges by title, seniority, and geography
- Top hiring companies and industries
- Job posting volume trends

## Stack
- **Ingestion:** Python + Adzuna API
- **Storage:** PostgreSQL (Docker)
- **Processing:** Pandas + SQLAlchemy
- **Analysis:** Jupyter Notebooks + Matplotlib / Seaborn / Plotly

## Setup

### 1. Clone & install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure credentials
```bash
cp .env.example .env
# Edit .env with your Adzuna App ID and App Key
# Get them at https://developer.adzuna.com
```

### 3. Start the database
```bash
docker-compose up -d
```

### 4. Run the ingestion pipeline
```bash
python pipeline.py
```

### 5. Open the analysis notebooks
```bash
jupyter notebook notebooks/
```
