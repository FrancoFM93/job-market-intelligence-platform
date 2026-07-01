"""
Main ingestion pipeline.
Run this to fetch jobs from Adzuna and load them into the database.
"""

import logging

from logger import setup_logging
from db.connection import init_db, SessionLocal

from ingestion.api_client import fetch_all_roles
from processing.transform import parse_job

# Warehouse loaders
from warehouse.load_dim_company import load_dim_company
from warehouse.load_dim_job import load_dim_job
from warehouse.load_dim_location import load_dim_location
from warehouse.load_dim_date import load_dim_date
from warehouse.load_fact_job_listing import load_fact_job_listing


logger = logging.getLogger(__name__)


def run(max_pages_per_role: int = 5) -> None:
    logger.info("Starting ingestion pipeline")

    # -------------------------
    # INIT DB
    # -------------------------
    logger.info("Initializing database...")
    init_db()

    # -------------------------
    # FETCH RAW DATA
    # -------------------------
    logger.info("Fetching jobs from Adzuna API...")
    raw_jobs = fetch_all_roles(max_pages_per_role=max_pages_per_role)
    logger.info("Total records fetched from API: %d", len(raw_jobs))

    # -------------------------
    # DB SESSION
    # -------------------------
    session = SessionLocal()

    inserted = 0
    skipped = 0
    errors = 0

    try:
        # -------------------------
        # PRELOAD DIMENSIONS
        # -------------------------
        logger.info("Loading dimension caches...")

        company_cache = load_dim_company(session)

        logger.info("Dimension caches loaded")

        # -------------------------
        # PROCESS ROWS
        # -------------------------
        logger.info("Processing records...")

        for raw in raw_jobs:
            try:
                job = parse_job(raw)
            except Exception as e:
                logger.warning(
                    "Failed to parse job record (id=%s): %s",
                    raw.get("id"),
                    e
                )
                errors += 1
                continue

            # Skip invalid
            if job.id is None:
                skipped += 1
                continue

            # Optional raw dedup (still fine to keep)
            exists = session.get(type(job), job.id)
            if exists:
                skipped += 1
                continue

            try:
                # -------------------------
                # NORMALIZATION
                # -------------------------
                company_name = job.company.strip() if job.company else None

                # -------------------------
                # DIMENSIONS
                # -------------------------
                company_key = company_cache.get(company_name)

                if company_key is None:
                    # fallback safety (should not normally happen)
                    company_cache = load_dim_company(session)
                    company_key = company_cache.get(company_name)

                job_key = load_dim_job(session, job.__dict__)

                location_key = load_dim_location(
                    session,
                    job.location_display,
                    job.location_area
                )

                date_key = load_dim_date(
                    session,
                    job.created_at.date()
                )

                # -------------------------
                # FACT TABLE
                # -------------------------
                load_fact_job_listing(
                    session,
                    company_key=company_key,
                    job_key=job_key,
                    location_key=location_key,
                    date_key=date_key,
                    salary_min=job.salary_min,
                    salary_max=job.salary_max
                )

                # -------------------------
                # OPTIONAL RAW STORAGE
                # -------------------------
                session.add(job)

                inserted += 1

            except Exception as e:
                logger.exception(
                    "Failed processing job id=%s: %s",
                    getattr(job, "id", None),
                    e
                )
                errors += 1
                continue

        # -------------------------
        # COMMIT BATCH
        # -------------------------
        session.commit()

        logger.info(
            "Pipeline complete — inserted: %d | skipped: %d | errors: %d",
            inserted,
            skipped,
            errors
        )

    except Exception as e:
        session.rollback()
        logger.exception("Pipeline failed: %s", e)
        raise

    finally:
        session.close()


if __name__ == "__main__":
    setup_logging(level="INFO")
    run()