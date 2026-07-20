from types import SimpleNamespace

import pipeline


def test_pipeline_rejects_invalid_record_before_parsing(mocker):
    raw_job = {
        "id": "adzuna-123",
        "title": "   ",
        "location": {
            "display_name": "Remote",
        },
        "created": "2026-05-20T12:00:00Z",
    }

    session = mocker.Mock()

    mocker.patch.object(
        pipeline,
        "init_db",
    )
    mocker.patch.object(
        pipeline,
        "fetch_all_roles",
        return_value=[raw_job],
    )
    mocker.patch.object(
        pipeline,
        "SessionLocal",
        return_value=session,
    )
    mock_parse_job = mocker.patch.object(
        pipeline,
        "parse_job",
    )

    pipeline.run(max_pages_per_role=1)

    mock_parse_job.assert_not_called()
    session.get.assert_not_called()
    session.add.assert_not_called()

    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()
    session.close.assert_called_once_with()


def test_pipeline_inserts_valid_new_record(
    mocker,
    sample_raw_job,
):
    parsed_job = SimpleNamespace(
        source_listing_id="123",
    )

    session = mocker.Mock()
    session.get.return_value = None

    mocker.patch.object(
        pipeline,
        "init_db",
    )
    mocker.patch.object(
        pipeline,
        "fetch_all_roles",
        return_value=[sample_raw_job],
    )
    mock_parse_job = mocker.patch.object(
        pipeline,
        "parse_job",
        return_value=parsed_job,
    )
    mocker.patch.object(
        pipeline,
        "SessionLocal",
        return_value=session,
    )

    pipeline.run(max_pages_per_role=1)

    mock_parse_job.assert_called_once_with(sample_raw_job)
    session.get.assert_called_once_with(
        type(parsed_job),
        "123",
    )
    session.add.assert_called_once_with(parsed_job)

    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()
    session.close.assert_called_once_with()


def test_pipeline_skips_valid_existing_record(
    mocker,
    sample_raw_job,
):
    parsed_job = SimpleNamespace(
        source_listing_id="123",
    )

    existing_job = SimpleNamespace(
        source_listing_id="123",
    )

    session = mocker.Mock()
    session.get.return_value = existing_job

    mocker.patch.object(
        pipeline,
        "init_db",
    )
    mocker.patch.object(
        pipeline,
        "fetch_all_roles",
        return_value=[sample_raw_job],
    )
    mocker.patch.object(
        pipeline,
        "parse_job",
        return_value=parsed_job,
    )
    mocker.patch.object(
        pipeline,
        "SessionLocal",
        return_value=session,
    )

    pipeline.run(max_pages_per_role=1)

    session.get.assert_called_once_with(
        type(parsed_job),
        "123",
    )
    session.add.assert_not_called()

    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()
    session.close.assert_called_once_with()