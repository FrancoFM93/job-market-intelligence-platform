"""
Main ingestion pipeline.
Run this to fetch jobs from Adzuna and load them into the database.

Usage:
    python pipeline.py
"""
import logging

from logger import setup_logging
from db.connection import init_db, SessionLocal
from ingestion.api_client import fetch_all_roles
from processing.transform import parse_job

logger = logging.getLogger(__name__)


def run(max_pages_per_role: int = 5) -> None:
    logger.info("Starting ingestion pipeline")

    logger.info("Initializing database...")
    init_db()

    logger.info("Fetching jobs from Adzuna API...")
    raw_jobs = fetch_all_roles(max_pages_per_role=max_pages_per_role)
    logger.info("Total records fetched from API: %d", len(raw_jobs))

    logger.info("Loading into database...")
    session = SessionLocal()
    inserted = 0
    skipped = 0
    errors = 0

    try:
        for raw in raw_jobs:
            try:
                job = parse_job(raw)
            except Exception as e:
                logger.warning("Failed to parse job record (id=%s): %s", raw.get("id"), e)
                errors += 1
                continue

            if job.id is None:
                logger.debug("Skipping record with null id: %s", raw.get("title"))
                skipped += 1
                continue

            exists = session.get(type(job), job.id)
            if exists:
                skipped += 1
                continue

            session.add(job)
            inserted += 1

        session.commit()
        logger.info("Pipeline complete — inserted: %d | skipped: %d | errors: %d",
                    inserted, skipped, errors)

    except Exception as e:
        session.rollback()
        logger.exception("Pipeline failed during database load: %s", e)
        raise

    finally:
        session.close()


if __name__ == "__main__":
    setup_logging(level="INFO")
    run()