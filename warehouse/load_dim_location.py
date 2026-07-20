from sqlalchemy.orm import Session
from warehouse.warehouse_models import DimLocation


def load_dim_location(
    session: Session,
    location_display: str,
    location_area: str | None
) -> int:
    """
    Inserts or retrieves a location dimension record.
    Returns location_key.
    """

    existing = (
        session.query(DimLocation)
        .filter_by(
            location_display=location_display,
            location_area=location_area
        )
        .first()
    )

    if existing:
        return existing.location_key

    location = DimLocation(
        location_display=location_display,
        location_area=location_area
    )

    session.add(location)
    session.flush()

    return location.location_key