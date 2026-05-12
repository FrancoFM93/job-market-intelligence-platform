import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base

load_dotenv()

logger = logging.getLogger(__name__)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "jobmarket")
DB_USER = os.getenv("DB_USER", "jobmarket")
DB_PASSWORD = os.getenv("DB_PASSWORD", "jobmarket")

DATABASE_URL = f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    """Create all tables if they don't exist."""
    logger.debug("Running init_db against %s:%s/%s", DB_HOST, DB_PORT, DB_NAME)
    Base.metadata.create_all(engine)
    logger.info("Database tables verified / created.")