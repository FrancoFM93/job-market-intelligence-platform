from db.connection import SessionLocal
from db.models import JobListing

from warehouse.fact_models import FactJobListing
from warehouse.load_dim_company import load_dim_company
from warehouse.load_dim_job import load_dim_job
from warehouse.load_dim_location import load_dim_location
from warehouse.load_dim_date import load_dim_date
from warehouse.load_fact_job_listing import load_fact_job_listing


def build_warehouse() -> None:
    session = SessionLocal()

    inserted = 0
    skipped = 0

    try:
        print("Loading DimCompany...")

        company_cache = load_dim_company(session)

        print("Loading existing fact IDs...")

        existing_source_ids = {
            source_listing_id
            for (source_listing_id,) in session.query(
                FactJobListing.source_listing_id
            ).all()
        }

        print("Building warehouse...")

        jobs = session.query(JobListing).all()

        for job in jobs:
            if job.source_listing_id in existing_source_ids:
                skipped += 1
                continue

            company_name = (
                job.company.strip()
                if job.company
                else None
            )

            company_key = company_cache.get(company_name)

            job_key = load_dim_job(
                session,
                job.title
            )

            location_key = load_dim_location(
                session,
                job.location_display,
                job.location_area
            )

            date_key = load_dim_date(
                session,
                job.created.date()
            )

            load_fact_job_listing(
                session=session,
                source_listing_id=job.source_listing_id,
                company_key=company_key,
                job_key=job_key,
                location_key=location_key,
                date_key=date_key,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
            )

            existing_source_ids.add(job.source_listing_id)
            inserted += 1

        session.commit()

        print(
            "Warehouse build complete - "
            f"inserted: {inserted} | skipped: {skipped}"
        )

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    build_warehouse()