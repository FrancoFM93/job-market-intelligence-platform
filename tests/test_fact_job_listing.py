from datetime import datetime
from types import SimpleNamespace

import pytest
from sqlalchemy import String, UniqueConstraint

import warehouse.build_warehouse as warehouse_builder
from warehouse.fact_models import FactJobListing
from warehouse.load_fact_job_listing import load_fact_job_listing


class RecordingSession:
    def __init__(self):
        self.added = []

    def add(self, instance):
        self.added.append(instance)

    def flush(self):
        self.added[-1].fact_id = 1


def test_fact_model_declares_source_listing_identity_and_uniqueness():
    table = FactJobListing.__table__
    source_id_column = table.c.source_listing_id

    assert isinstance(source_id_column.type, String)
    assert source_id_column.nullable is False

    source_id_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
        and list(constraint.columns.keys()) == ["source_listing_id"]
    ]

    assert len(source_id_constraints) == 1
    assert (
        source_id_constraints[0].name
        == "uq_fact_job_listing_source_listing_id"
    )


def test_fact_model_preserves_dimension_foreign_keys():
    foreign_keys = {
        foreign_key.parent.name: foreign_key.target_fullname
        for foreign_key in FactJobListing.__table__.foreign_keys
    }

    assert foreign_keys == {
        "company_key": "dim_company.company_key",
        "job_key": "dim_job.job_key",
        "location_key": "dim_location.location_key",
        "date_key": "dim_date.date_key",
    }


def test_fact_loader_persists_source_listing_id():
    session = RecordingSession()

    fact_id = load_fact_job_listing(
        session,
        source_listing_id="adzuna-123",
        company_key=1,
        job_key=2,
        location_key=3,
        date_key=20260718,
        salary_min=90000,
        salary_max=120000,
    )

    assert fact_id == 1
    assert len(session.added) == 1
    assert session.added[0].source_listing_id == "adzuna-123"


def test_fact_loader_rejects_missing_source_listing_id():
    session = RecordingSession()

    with pytest.raises(ValueError, match="source listing ID is required"):
        load_fact_job_listing(
            session,
            source_listing_id="",
            company_key=1,
            job_key=2,
            location_key=3,
            date_key=20260718,
        )

    assert session.added == []


def test_warehouse_builder_forwards_source_listing_id(mocker):
    job = SimpleNamespace(
        source_listing_id="adzuna-123",
        company="Example Company",
        title="Data Engineer",
        location_display="Remote",
        location_area=None,
        created=datetime(2026, 7, 18),
        salary_min=90000,
        salary_max=120000,
    )
    session = mocker.Mock()
    session.query.return_value.all.return_value = [job]

    mocker.patch.object(
        warehouse_builder,
        "SessionLocal",
        return_value=session,
    )
    mocker.patch.object(
        warehouse_builder,
        "load_dim_company",
        return_value={"Example Company": 1},
    )
    mocker.patch.object(warehouse_builder, "load_dim_job", return_value=2)
    mocker.patch.object(warehouse_builder, "load_dim_location", return_value=3)
    mocker.patch.object(warehouse_builder, "load_dim_date", return_value=20260718)
    mock_fact_loader = mocker.patch.object(
        warehouse_builder,
        "load_fact_job_listing",
    )

    warehouse_builder.build_warehouse()

    mock_fact_loader.assert_called_once_with(
        session=session,
        source_listing_id="adzuna-123",
        company_key=1,
        job_key=2,
        location_key=3,
        date_key=20260718,
        salary_min=90000,
        salary_max=120000,
    )
    session.commit.assert_called_once_with()
    session.close.assert_called_once_with()
