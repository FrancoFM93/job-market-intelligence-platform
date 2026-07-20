from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import math
from typing import Any


@dataclass
class ValidationResult:
    """Result returned after validating a raw job listing."""

    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


def _is_blank(value: Any) -> bool:
    """Return True when a required text-like value is missing or blank."""
    return value is None or not str(value).strip()


def _validate_required_fields(raw: dict, errors: list[str]) -> None:
    if _is_blank(raw.get("id")):
        errors.append("source listing ID is required")

    if _is_blank(raw.get("title")):
        errors.append("title is required")

    location = raw.get("location")

    if not isinstance(location, dict) or _is_blank(
        location.get("display_name")
    ):
        errors.append("location display name is required")


def _validate_created_date(raw: dict, errors: list[str]) -> None:
    created_value = raw.get("created")

    if _is_blank(created_value):
        errors.append("created date is required")
        return

    try:
        created = datetime.fromisoformat(
            str(created_value).replace("Z", "+00:00")
        )
    except ValueError:
        errors.append("created date must be valid ISO-8601")
        return

    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)

    maximum_allowed = datetime.now(timezone.utc) + timedelta(days=1)

    if created.astimezone(timezone.utc) > maximum_allowed:
        errors.append(
            "created date cannot be more than one day in the future"
        )


def _parse_salary(
    field_name: str,
    value: Any,
    errors: list[str],
) -> float | None:
    if value is None:
        return None

    try:
        salary = float(value)
    except (TypeError, ValueError):
        errors.append(f"{field_name} must be numeric")
        return None

    if not math.isfinite(salary):
        errors.append(f"{field_name} must be finite")
        return None

    if salary < 0:
        errors.append(f"{field_name} cannot be negative")
        return None

    return salary


def _validate_salary(raw: dict, errors: list[str]) -> None:
    salary_min = _parse_salary(
        "salary_min",
        raw.get("salary_min"),
        errors,
    )
    salary_max = _parse_salary(
        "salary_max",
        raw.get("salary_max"),
        errors,
    )

    if (
        salary_min is not None
        and salary_max is not None
        and salary_min > salary_max
    ):
        errors.append("salary_min cannot exceed salary_max")


def validate_raw_job(raw: dict) -> ValidationResult:
    """Validate a raw Adzuna job record using pipeline business rules."""
    errors: list[str] = []

    _validate_required_fields(raw, errors)
    _validate_created_date(raw, errors)
    _validate_salary(raw, errors)

    return ValidationResult(errors=errors)