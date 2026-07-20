from datetime import datetime
from sqlalchemy import (
    Column, String, Float, DateTime, Text
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class JobListing(Base):
    __tablename__ = "job_listings"

    source_listing_id = Column(String, primary_key=True)  # Adzuna's own ID
    title = Column(String, nullable=False)
    company = Column(String)
    location_display = Column(String)
    location_area = Column(String)                  # state / metro area
    description = Column(Text)
    category = Column(String)
    contract_type = Column(String)                  # full_time, part_time, etc.
    contract_time = Column(String)                  # permanent, contract, etc.
    salary_min = Column(Float)
    salary_max = Column(Float)
    salary_is_predicted = Column(String)            # '0' or '1' from Adzuna
    redirect_url = Column(String)
    search_role = Column(String)                    # which query returned this
    created = Column(DateTime)                      # Adzuna's posted date
    fetched_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<JobListing {self.source_listing_id}: "
            f"{self.title} @ {self.company}>"
        )
