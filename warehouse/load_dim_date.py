from sqlalchemy.orm import Session
from datetime import date
from warehouse.warehouse_models import DimDate


def load_dim_date(session: Session, dt: date) -> int:
    """
    Inserts or retrieves a date dimension record.
    Returns date_key (YYYYMMDD).
    """

    date_key = int(dt.strftime("%Y%m%d"))

    existing = (
        session.query(DimDate)
        .filter_by(date_key=date_key)
        .first()
    )

    if existing:
        return existing.date_key

    dim = DimDate(
        date_key=date_key,
        full_date=dt,
        year=dt.year,
        month=dt.month,
        day=dt.day,
        weekday=dt.strftime("%A"),
        month_name=dt.strftime("%B"),
    )

    session.add(dim)
    session.flush()

    return dim.date_key