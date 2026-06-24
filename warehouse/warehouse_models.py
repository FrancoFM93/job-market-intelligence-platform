from sqlalchemy import Column, Integer, String
from db.models import Base


class DimCompany(Base):
    __tablename__ = "dim_company"

    company_key = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String, unique=True, nullable=False)