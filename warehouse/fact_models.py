from sqlalchemy import Column, Integer, Float, ForeignKey, String, UniqueConstraint
from db.models import Base


class FactJobListing(Base):
    __tablename__ = "fact_job_listing"

    fact_id = Column(Integer, primary_key=True, autoincrement=True)
    source_listing_id = Column(String, nullable=False)

    company_key = Column(Integer, ForeignKey("dim_company.company_key"))
    job_key = Column(Integer, ForeignKey("dim_job.job_key"))
    location_key = Column(Integer, ForeignKey("dim_location.location_key"))
    date_key = Column(Integer, ForeignKey("dim_date.date_key"))

    salary_min = Column(Float)
    salary_max = Column(Float)

    __table_args__ = (
        UniqueConstraint(
            "source_listing_id",
            name="uq_fact_job_listing_source_listing_id",
        ),
    )
