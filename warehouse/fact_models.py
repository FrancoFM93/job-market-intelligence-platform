from sqlalchemy import Column, Integer, Float, ForeignKey, String
from db.models import Base


class FactJobListing(Base):
    __tablename__ = "fact_job_listing"

    fact_id = Column(Integer, primary_key=True, autoincrement=True)

    company_key = Column(Integer, ForeignKey("dim_company.company_key"))
    job_key = Column(Integer, ForeignKey("dim_job.job_key"))
    location_key = Column(Integer, ForeignKey("dim_location.location_key"))
    date_key = Column(Integer, ForeignKey("dim_date.date_key"))

    salary_min = Column(Float)
    salary_max = Column(Float)

    contract_type = Column(String)
    contract_time = Column(String)





