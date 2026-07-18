import logging

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import get_database_config
from db.models import Base

from warehouse.warehouse_models import (DimCompany, DimJob, DimLocation, DimDate,)
from warehouse.fact_models import FactJobListing

load_dotenv()

logger = logging.getLogger(__name__)

database_config = get_database_config()
engine = create_engine(database_config.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    """Create all tables if they don't exist."""
    logger.debug(
        "Running init_db against %s:%s/%s",
        database_config.host,
        database_config.port,
        database_config.name,
    )
    Base.metadata.create_all(engine)
    logger.info("Database tables verified / created.")
