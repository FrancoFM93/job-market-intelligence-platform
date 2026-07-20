from datetime import datetime, timedelta, timezone

import pytest

from processing.validation import validate_raw_job


def test_valid_raw_job_passes_validation(sample_raw_job):
    result = validate_raw_job(sample_raw_job)

    assert result.is_valid is True
    assert result.errors == []


@pytest.mark.parametrize(
    "invalid_id",
    [
        None,
        "",
        "   ",
    ],
)
def test_rejects_missing_or_blank_source_id(sample_raw_job, invalid_id):
    sample_raw_job["id"] = invalid_id

    result = validate_raw_job(sample_raw_job)

    assert result.is_valid is False
    assert "source listing ID is required" in result.errors


@pytest.mark.parametrize(
    "invalid_title",
    [
        None,
        "",
        "   ",
    ],
)
def test_rejects_missing_or_blank_title(sample_raw_job, invalid_title):
    sample_raw_job["title"] = invalid_title

    result = validate_raw_job(sample_raw_job)

    assert result.is_valid is False
    assert "title is required" in result.errors


@pytest.mark.parametrize(
    "invalid_location",
    [
        None,
        {},
        {"display_name": None},
        {"display_name": ""},
        {"display_name": "   "},
    ],
)
def test_rejects_missing_or_blank_location_display(
    sample_raw_job,
    invalid_location,
):
    sample_raw_job["location"] = invalid_location

    result = validate_raw_job(sample_raw_job)

    assert result.is_valid is False
    assert "location display name is required" in result.errors


def test_rejects_missing_created_date(sample_raw_job):
    sample_raw_job["created"] = None

    result = validate_raw_job(sample_raw_job)

    assert result.is_valid is False
    assert "created date is required" in result.errors


def test_rejects_invalid_created_date(sample_raw_job):
    sample_raw_job["created"] = "not-a-date"

    result = validate_raw_job(sample_raw_job)

    assert result.is_valid is False
    assert "created date must be valid ISO-8601" in result.errors


def test_rejects_created_date_more_than_one_day_in_future(sample_raw_job):
    future_date = datetime.now(timezone.utc) + timedelta(days=2)
    sample_raw_job["created"] = future_date.isoformat()

    result = validate_raw_job(sample_raw_job)

    assert result.is_valid is False
    assert "created date cannot be more than one day in the future" in result.errors


def test_allows_created_date_within_one_day_future_tolerance(sample_raw_job):
    future_date = datetime.now(timezone.utc) + timedelta(hours=12)
    sample_raw_job["created"] = future_date.isoformat()

    result = validate_raw_job(sample_raw_job)

    assert result.is_valid is True
    assert result.errors == []


@pytest.mark.parametrize(
    "field_name",
    [
        "salary_min",
        "salary_max",
    ],
)
def test_rejects_non_numeric_salary(sample_raw_job, field_name):
    sample_raw_job[field_name] = "not-a-number"

    result = validate_raw_job(sample_raw_job)

    assert result.is_valid is False
    assert f"{field_name} must be numeric" in result.errors


@pytest.mark.parametrize(
    "field_name",
    [
        "salary_min",
        "salary_max",
    ],
)
def test_rejects_negative_salary(sample_raw_job, field_name):
    sample_raw_job[field_name] = -1

    result = validate_raw_job(sample_raw_job)

    assert result.is_valid is False
    assert f"{field_name} cannot be negative" in result.errors


@pytest.mark.parametrize(
    "invalid_value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
@pytest.mark.parametrize(
    "field_name",
    [
        "salary_min",
        "salary_max",
    ],
)
def test_rejects_non_finite_salary(
    sample_raw_job,
    field_name,
    invalid_value,
):
    sample_raw_job[field_name] = invalid_value

    result = validate_raw_job(sample_raw_job)

    assert result.is_valid is False
    assert f"{field_name} must be finite" in result.errors


def test_rejects_salary_min_greater_than_salary_max(sample_raw_job):
    sample_raw_job["salary_min"] = 150000
    sample_raw_job["salary_max"] = 100000

    result = validate_raw_job(sample_raw_job)

    assert result.is_valid is False
    assert "salary_min cannot exceed salary_max" in result.errors


def test_allows_missing_salary_values(sample_raw_job):
    sample_raw_job["salary_min"] = None
    sample_raw_job["salary_max"] = None

    result = validate_raw_job(sample_raw_job)

    assert result.is_valid is True
    assert result.errors == []


def test_collects_multiple_validation_errors(sample_raw_job):
    sample_raw_job["id"] = ""
    sample_raw_job["title"] = " "
    sample_raw_job["location"] = {}
    sample_raw_job["created"] = "invalid-date"
    sample_raw_job["salary_min"] = -100

    result = validate_raw_job(sample_raw_job)

    assert result.is_valid is False
    assert len(result.errors) == 5
    assert "source listing ID is required" in result.errors
    assert "title is required" in result.errors
    assert "location display name is required" in result.errors
    assert "created date must be valid ISO-8601" in result.errors
    assert "salary_min cannot be negative" in result.errors