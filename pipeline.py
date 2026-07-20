"""
Main ingestion pipeline.

Fetches job listings from the Adzuna API, validates the source records,
and stores valid new listings in the operational PostgreSQL table.

The dimensional warehouse is built separately with:

    py -m warehouse.build_warehouse
"""

from collections import Counter
import logging

from db.connection import SessionLocal, init_db
from ingestion.api_client import fetch_all_roles
from logger import setup_logging
from processing.transform import parse_job
from processing.validation import validate_raw_job

logger = logging.getLogger(__name__)


def run(max_pages_per_role: int = 5) -> None:
    logger.info("Starting ingestion pipeline")

    logger.info("Initializing database...")
    init_db()

    logger.info("Fetching jobs from Adzuna API...")
    raw_jobs = fetch_all_roles(
        max_pages_per_role=max_pages_per_role,
    )

    logger.info(
        "Total records fetched from API: %d",
        len(raw_jobs),
    )

    session = SessionLocal()

    inserted = 0
    skipped = 0
    rejected = 0
    errors = 0

    rejection_reasons: Counter[str] = Counter()

    try:
        for raw in raw_jobs:
            validation_result = validate_raw_job(raw)

            if not validation_result.is_valid:
                rejected += 1
                rejection_reasons.update(validation_result.errors)

                logger.warning(
                    "Rejected job record (id=%s): %s",
                    raw.get("id"),
                    "; ".join(validation_result.errors),
                )
                continue

            try:
                job = parse_job(raw)

            except Exception as error:
                logger.warning(
                    "Failed to parse job record (id=%s): %s",
                    raw.get("id"),
                    error,
                )
                errors += 1
                continue

            existing_job = session.get(
                type(job),
                job.source_listing_id,
            )

            if existing_job:
                skipped += 1
                continue

            session.add(job)
            inserted += 1

        session.commit()

        logger.info(
            "Pipeline complete - inserted: %d | skipped: %d | "
            "rejected: %d | errors: %d",
            inserted,
            skipped,
            rejected,
            errors,
        )

        if rejection_reasons:
            logger.info("Validation rejection summary:")

            for reason, count in rejection_reasons.most_common():
                logger.info(
                    "  %s: %d",
                    reason,
                    count,
                )

    except Exception as error:
        session.rollback()

        logger.exception(
            "Pipeline failed during database load: %s",
            error,
        )

        raise

    finally:
        session.close()


if __name__ == "__main__":
    setup_logging(level="INFO")
    run()