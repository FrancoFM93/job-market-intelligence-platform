from sqlalchemy.orm import Session

from warehouse.fact_models import FactJobListing
from warehouse.warehouse_models import DimCompany, DimJob, DimLocation, DimDate


def load_fact_job_listing(
    session: Session,
    source_listing_id: str,
    company_key: int,
    job_key: int,
    location_key: int,
    date_key: int,
    salary_min: float | None = None,
    salary_max: float | None = None
) -> int:
    """
    Inserts a fact record for a job listing.
    Returns fact_id.
    """
    if not source_listing_id or not source_listing_id.strip():
        raise ValueError("A source listing ID is required to load a fact row.")

    fact = FactJobListing(
        source_listing_id=source_listing_id,
        company_key=company_key,
        job_key=job_key,
        location_key=location_key,
        date_key=date_key,
        salary_min=salary_min,
        salary_max=salary_max,
    )

    session.add(fact)
    session.flush()

    return fact.fact_id
