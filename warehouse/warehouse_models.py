from sqlalchemy import Column, Integer, String
from db.models import Base


class DimCompany(Base):
    __tablename__ = "dim_company"

    company_key = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String, unique=True, nullable=False)


class DimLocation(Base):
    __tablename__ = "dim_location"

    location_key = Column(Integer, primary_key=True, autoincrement=True)

    location_display = Column(String, nullable=False)
    location_area = Column(String, nullable=True)


class DimJob(Base):
    __tablename__ = "dim_job"

    job_key = Column(Integer, primary_key=True, autoincrement=True)

    title = Column(String, nullable=False)
    category = Column(String)
    
    contract_type = Column(String)
    contract_time = Column(String)

    location_display = Column(String)
    location_area = Column(String)

    salary_min = Column(Float)
    salary_max = Column(Float)

    created_at = Column(DateTime)