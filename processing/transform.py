from datetime import datetime
from db.models import JobListing


def parse_job(raw: dict) -> JobListing:
    """Convert a raw Adzuna API result dict into a JobListing model instance."""
    location = raw.get("location", {})
    location_area = None
    areas = location.get("area", [])
    if areas:
        # Adzuna returns area as a list: ["US", "State", "City"]
        location_area = areas[-1] if len(areas) >= 1 else None

    salary_min = raw.get("salary_min")
    salary_max = raw.get("salary_max")

    created_str = raw.get("created")
    created = None
    if created_str:
        try:
            created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
        except ValueError:
            pass

    return JobListing(
        id=raw.get("id"),
        title=raw.get("title"),
        company=raw.get("company", {}).get("display_name"),
        location_display=location.get("display_name"),
        location_area=location_area,
        description=raw.get("description"),
        category=raw.get("category", {}).get("label"),
        contract_type=raw.get("contract_type"),
        contract_time=raw.get("contract_time"),
        salary_min=float(salary_min) if salary_min is not None else None,
        salary_max=float(salary_max) if salary_max is not None else None,
        salary_is_predicted=raw.get("salary_is_predicted"),
        redirect_url=raw.get("redirect_url"),
        search_role=raw.get("search_role"),
        created=created,
    )
