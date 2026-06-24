from sqlalchemy.orm import Session
from sqlalchemy import select
from db.connection import SessionLocal
from db.models import JobListing
from warehouse.warehouse_models import DimCompany


def load_dim_company():
    """
    Loads unique companies from the raw job_listings table
    into the dim_company dimension table.

    Returns:
        dict: Mapping of company_name -> company_key
    """

    session: Session = SessionLocal()

    try:
        print("Loading DimCompany...")

        # 1. Extract distinct company names from raw table
        companies = session.execute(
            select(JobListing.company).distinct()
        ).scalars().all()

        # 2. Clean null or empty values
        companies = [c for c in companies if c]

        company_mapping = {}

        for company_name in companies:

            # 3. Check if company already exists in dimension
            existing_company = session.execute(
                select(DimCompany).where(DimCompany.company_name == company_name)
            ).scalar_one_or_none()

            # 4. If exists, reuse its key
            if existing_company:
                company_mapping[company_name] = existing_company.company_key
                continue

            # 5. Insert new dimension record
            new_company = DimCompany(company_name=company_name)
            session.add(new_company)

            # Flush to get generated primary key without committing
            session.flush()

            company_mapping[company_name] = new_company.company_key

        # 6. Commit all changes
        session.commit()

        print(f"DimCompany loaded successfully: {len(company_mapping)} records")

        return company_mapping

    except Exception as e:
        session.rollback()
        raise e

    finally:
        session.close()