from sqlalchemy.orm import Session

from warehouse.warehouse_models import DimJob


def load_dim_job(session: Session, title: str) -> int:
    """
    Inserts or retrieves a job title.
    Returns job_key.
    """

    normalized_title = title.strip().lower()

    existing = (
        session.query(DimJob)
        .filter_by(title=normalized_title)
        .first()
    )

    if existing:
        return existing.job_key

    job = DimJob(
        title=normalized_title
    )

    session.add(job)
    session.flush()

    return job.job_key