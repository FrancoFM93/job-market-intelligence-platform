from sqlalchemy.orm import Session
from sqlalchemy import select
from db.models import JobListing
from warehouse.warehouse_models import DimCompany


def load_dim_company(session: Session) -> dict:
    """
    Loads unique companies from raw JobListing table into DimCompany.
    Returns mapping: company_name -> company_key
    """

    print("Loading DimCompany...")

    companies = session.execute(
        select(JobListing.company).distinct()
    ).scalars().all()

    companies = [c.strip() for c in companies if c]

    existing = {
        row.company_name: row.company_key
        for row in session.query(DimCompany).all()
    }

    mapping = dict(existing)

    for company_name in companies:
        if company_name in mapping:
            continue

        dim = DimCompany(company_name=company_name)
        session.add(dim)
        session.flush()

        mapping[company_name] = dim.company_key

    print(f"DimCompany loaded: {len(mapping)}")
    return mapping