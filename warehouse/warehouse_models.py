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

    job_key = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    title = Column(String, nullable=False)


class DimDate(Base):
    __tablename__ = "dim_date"

    date_key = Column(Integer, primary_key=True)  # YYYYMMDD format

    full_date = Column(Date, nullable=False)

    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)

    weekday = Column(String, nullable=False)
    month_name = Column(String, nullable=False)