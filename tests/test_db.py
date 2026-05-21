from db.models import JobListing


def test_job_listing_creation():
    job = JobListing(
        id="1",
        title="Data Scientist",
        company="OpenAI"
    )

    assert job.id == "1"
    assert job.title == "Data Scientist"
    assert job.company == "OpenAI"


def test_job_listing_repr():
    job = JobListing(
        id="99",
        title="ML Engineer",
        company="Anthropic"
    )

    result = repr(job)

    assert "ML Engineer" in result
    assert "Anthropic" in result