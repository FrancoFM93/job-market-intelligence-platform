import pytest

from processing.transform import parse_job


def test_parse_job_success(sample_raw_job):
    job = parse_job(sample_raw_job)

    assert job.source_listing_id == "123"
    assert job.title == "Data Engineer"
    assert job.company == "OpenAI"
    assert job.location_area == "San Francisco"
    assert job.salary_min == 90000.0
    assert job.salary_max == 120000.0
    assert job.search_role == "data engineer"
    assert job.created is not None


def test_parse_job_missing_optional_fields():
    raw = {
        "id": "456",
        "title": "Analyst"
    }

    job = parse_job(raw)

    assert job.company is None
    assert job.salary_min is None
    assert job.location_area is None
    assert job.created is None


def test_parse_job_invalid_date(sample_raw_job):
    sample_raw_job["created"] = "invalid-date"

    job = parse_job(sample_raw_job)

    assert job.created is None


def test_parse_job_empty_area(sample_raw_job):
    sample_raw_job["location"]["area"] = []

    job = parse_job(sample_raw_job)

    assert job.location_area is None


def test_parse_job_salary_conversion(sample_raw_job):
    sample_raw_job["salary_min"] = "95000"
    sample_raw_job["salary_max"] = "130000"

    job = parse_job(sample_raw_job)

    assert isinstance(job.salary_min, float)
    assert isinstance(job.salary_max, float)


def test_parse_job_rejects_missing_source_listing_id():
    with pytest.raises(ValueError, match="required Adzuna source ID"):
        parse_job({"title": "Data Engineer"})
