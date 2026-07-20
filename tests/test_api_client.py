from unittest.mock import call

import pytest
import requests

from ingestion.api_client import (
    BASE_URL,
    RESULTS_PER_PAGE,
    fetch_all_jobs,
    fetch_jobs,
)


DUMMY_APP_ID = "test-app-id"
DUMMY_APP_KEY = "test-app-key"


def test_fetch_jobs_success(mocker, monkeypatch):
    monkeypatch.delenv("ADZUNA_APP_ID", raising=False)
    monkeypatch.delenv("ADZUNA_APP_KEY", raising=False)

    mock_response = mocker.Mock()
    mock_response.json.return_value = {"results": [{"id": "1"}]}
    mock_response.raise_for_status.return_value = None

    mock_get = mocker.patch(
        "ingestion.api_client.requests.get",
        return_value=mock_response
    )

    result = fetch_jobs(
        "data engineer",
        page=1,
        app_id=DUMMY_APP_ID,
        app_key=DUMMY_APP_KEY,
    )

    assert result == {"results": [{"id": "1"}]}
    mock_get.assert_called_once_with(
        f"{BASE_URL}/1",
        params={
            "app_id": DUMMY_APP_ID,
            "app_key": DUMMY_APP_KEY,
            "results_per_page": RESULTS_PER_PAGE,
            "what": "data engineer",
            "content-type": "application/json",
        },
        timeout=10,
    )


def test_fetch_jobs_uses_environment_credentials_by_default(mocker, monkeypatch):
    monkeypatch.setenv("ADZUNA_APP_ID", DUMMY_APP_ID)
    monkeypatch.setenv("ADZUNA_APP_KEY", DUMMY_APP_KEY)

    mock_response = mocker.Mock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status.return_value = None
    mock_get = mocker.patch(
        "ingestion.api_client.requests.get",
        return_value=mock_response,
    )

    fetch_jobs("data analyst", page=2)

    request_params = mock_get.call_args.kwargs["params"]
    assert request_params["app_id"] == DUMMY_APP_ID
    assert request_params["app_key"] == DUMMY_APP_KEY


def test_fetch_jobs_http_error(mocker):
    mock_response = mocker.Mock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("API error")

    mock_get = mocker.patch(
        "ingestion.api_client.requests.get",
        return_value=mock_response
    )

    with pytest.raises(requests.HTTPError, match="API error"):
        fetch_jobs(
            "data engineer",
            app_id=DUMMY_APP_ID,
            app_key=DUMMY_APP_KEY,
        )

    mock_get.assert_called_once()


def test_fetch_all_jobs_stops_on_empty_results(mocker):
    mock_fetch = mocker.patch(
        "ingestion.api_client.fetch_jobs",
        return_value={"results": []}
    )
    mock_sleep = mocker.patch("ingestion.api_client.time.sleep")

    jobs = fetch_all_jobs(
        "data engineer",
        max_pages=5,
        app_id=DUMMY_APP_ID,
        app_key=DUMMY_APP_KEY,
    )

    assert jobs == []
    mock_fetch.assert_called_once_with(
        "data engineer",
        1,
        app_id=DUMMY_APP_ID,
        app_key=DUMMY_APP_KEY,
    )
    mock_sleep.assert_not_called()


def test_fetch_all_jobs_collects_multiple_pages_without_sleeping(mocker):
    mock_fetch = mocker.patch(
        "ingestion.api_client.fetch_jobs",
        side_effect=[
            {"results": [{"id": "1"}]},
            {"results": [{"id": "2"}]},
            {"results": []},
        ]
    )
    mock_sleep = mocker.patch("ingestion.api_client.time.sleep")

    jobs = fetch_all_jobs(
        "data engineer",
        max_pages=5,
        app_id=DUMMY_APP_ID,
        app_key=DUMMY_APP_KEY,
    )

    assert jobs == [{"id": "1"}, {"id": "2"}]
    assert mock_fetch.call_args_list == [
        call(
            "data engineer",
            1,
            app_id=DUMMY_APP_ID,
            app_key=DUMMY_APP_KEY,
        ),
        call(
            "data engineer",
            2,
            app_id=DUMMY_APP_ID,
            app_key=DUMMY_APP_KEY,
        ),
        call(
            "data engineer",
            3,
            app_id=DUMMY_APP_ID,
            app_key=DUMMY_APP_KEY,
        ),
    ]
    assert mock_sleep.call_args_list == [call(0.5), call(0.5)]


def test_fetch_jobs_missing_credentials(mocker, monkeypatch):
    monkeypatch.delenv("ADZUNA_APP_ID", raising=False)
    monkeypatch.delenv("ADZUNA_APP_KEY", raising=False)
    mock_get = mocker.patch("ingestion.api_client.requests.get")

    with pytest.raises(EnvironmentError, match="ADZUNA_APP_ID and ADZUNA_APP_KEY"):
        fetch_jobs("data engineer")

    mock_get.assert_not_called()
