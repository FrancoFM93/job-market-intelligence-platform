from sqlalchemy.orm import Session
from warehouse.warehouse_models import DimJob


def load_dim_job(session: Session, job_data: dict) -> int:
    """
    Inserts or retrieves a job dimension record.
    Returns job_key.
    """

    title = job_data["title"].strip().lower()
    company_key = job_data.get("company_key")

    existing = (
        session.query(DimJob)
        .filter(
            DimJob.title == title,
            DimJob.company_key == company_key
        )
        .first()
    )

    if existing:
        return existing.job_key

    job = DimJob(
        title=title,
        company_key=company_key,
        category=job_data.get("category"),
        contract_type=job_data.get("contract_type"),
        contract_time=job_data.get("contract_time"),
        location_display=job_data.get("location_display"),
        location_area=job_data.get("location_area"),
        salary_min=job_data.get("salary_min"),
        salary_max=job_data.get("salary_max"),
        created_at=job_data.get("created_at"),
    )

    session.add(job)
    session.flush()

    return job.job_key