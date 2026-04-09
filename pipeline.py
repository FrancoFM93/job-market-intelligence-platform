"""
Main ingestion pipeline.
Run this to fetch jobs from Adzuna and load them into the database.

Usage:
    python pipeline.py
"""
from db.connection import init_db, SessionLocal
from ingestion.api_client import fetch_all_roles
from processing.transform import parse_job


def run(max_pages_per_role: int = 5):
    print("Initializing database...")
    init_db()

    print("\nFetching jobs from Adzuna API...")
    raw_jobs = fetch_all_roles(max_pages_per_role=max_pages_per_role)

    print("\nLoading into database...")
    session = SessionLocal()
    inserted = 0
    skipped = 0
    try:
        for raw in raw_jobs:
            job = parse_job(raw)
            if job.id is None:
                skipped += 1
                continue
            # Upsert: skip if already exists
            exists = session.get(type(job), job.id)
            if exists:
                skipped += 1
                continue
            session.add(job)
            inserted += 1
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    print(f"\nDone. Inserted: {inserted} | Skipped (duplicates): {skipped}")


if __name__ == "__main__":
    run()
