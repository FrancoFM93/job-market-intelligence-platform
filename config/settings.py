import os
from dataclasses import dataclass, field

from sqlalchemy.engine import URL


@dataclass(frozen=True)
class DatabaseConfig:
    """Immutable PostgreSQL connection settings."""

    host: str
    port: int
    name: str
    user: str
    password: str = field(repr=False)

    @property
    def database_url(self) -> URL:
        """Build a SQLAlchemy URL without manually interpolating credentials."""
        return URL.create(
            drivername="postgresql+pg8000",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.name,
        )


def get_database_config() -> DatabaseConfig:
    """Read the current environment and return PostgreSQL configuration."""
    raw_port = os.getenv("DB_PORT", "5433")

    try:
        port = int(raw_port)
    except ValueError as exc:
        raise ValueError("DB_PORT must be an integer.") from exc

    return DatabaseConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=port,
        name=os.getenv("DB_NAME", "jobmarket"),
        user=os.getenv("DB_USER", "jobmarket"),
        password=os.getenv("DB_PASSWORD", "jobmarket"),
    )
