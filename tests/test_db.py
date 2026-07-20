from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.models import JobListing


def test_job_listing_creation():
    job = JobListing(
        source_listing_id="1",
        title="Data Scientist",
        company="OpenAI"
    )

    assert job.source_listing_id == "1"
    assert job.title == "Data Scientist"
    assert job.company == "OpenAI"


def test_job_listing_repr():
    job = JobListing(
        source_listing_id="99",
        title="ML Engineer",
        company="Anthropic"
    )

    result = repr(job)

    assert "ML Engineer" in result
    assert "Anthropic" in result


def test_source_listing_id_is_persisted():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    JobListing.__table__.create(engine)

    with Session(engine) as session:
        session.add(
            JobListing(
                source_listing_id="adzuna-123",
                title="Data Engineer",
            )
        )
        session.commit()

    with Session(engine) as session:
        persisted_job = session.get(JobListing, "adzuna-123")

        assert persisted_job is not None
        assert persisted_job.source_listing_id == "adzuna-123"
