import pytest

from config.settings import DatabaseConfig, get_database_config


DATABASE_ENVIRONMENT_VARIABLES = (
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
)


def clear_database_environment(monkeypatch):
    for variable in DATABASE_ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(variable, raising=False)


def test_database_config_defaults(monkeypatch):
    clear_database_environment(monkeypatch)

    config = get_database_config()

    assert config == DatabaseConfig(
        host="localhost",
        port=5433,
        name="jobmarket",
        user="jobmarket",
        password="jobmarket",
    )


def test_database_config_uses_environment_overrides(monkeypatch):
    clear_database_environment(monkeypatch)
    monkeypatch.setenv("DB_HOST", "database.internal")
    monkeypatch.setenv("DB_NAME", "analytics")
    monkeypatch.setenv("DB_USER", "pipeline_user")
    monkeypatch.setenv("DB_PASSWORD", "override-password")

    config = get_database_config()

    assert config.host == "database.internal"
    assert config.name == "analytics"
    assert config.user == "pipeline_user"
    assert config.password == "override-password"


def test_database_config_converts_port_to_integer(monkeypatch):
    clear_database_environment(monkeypatch)
    monkeypatch.setenv("DB_PORT", "6543")

    config = get_database_config()

    assert config.port == 6543
    assert isinstance(config.port, int)


def test_database_url_construction():
    config = DatabaseConfig(
        host="database.internal",
        port=6543,
        name="analytics",
        user="pipeline_user",
        password="p@ssword:/value",
    )

    url = config.database_url

    assert url.drivername == "postgresql+pg8000"
    assert url.host == "database.internal"
    assert url.port == 6543
    assert url.database == "analytics"
    assert url.username == "pipeline_user"
    assert url.password == "p@ssword:/value"
    assert "p@ssword:/value" not in str(url)


def test_database_config_safe_representation_hides_password():
    password = "do-not-display-this-password"
    config = DatabaseConfig(
        host="localhost",
        port=5433,
        name="jobmarket",
        user="jobmarket",
        password=password,
    )

    assert password not in repr(config)
    assert password not in str(config)


def test_database_config_rejects_non_numeric_port(monkeypatch):
    clear_database_environment(monkeypatch)
    monkeypatch.setenv("DB_PORT", "not-a-port")

    with pytest.raises(ValueError, match="DB_PORT must be an integer"):
        get_database_config()
