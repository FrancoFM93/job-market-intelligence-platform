import requests

from ingestion.api_client import fetch_jobs, fetch_all_jobs


def test_fetch_jobs_success(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"results": [{"id": "1"}]}
    mock_response.raise_for_status.return_value = None

    mock_get = mocker.patch(
        "ingestion.api_client.requests.get",
        return_value=mock_response
    )

    result = fetch_jobs("data engineer", page=1)

    assert "results" in result
    mock_get.assert_called_once()


def test_fetch_jobs_http_error(mocker):
    mock_response = mocker.Mock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("API error")

    mocker.patch(
        "ingestion.api_client.requests.get",
        return_value=mock_response
    )

    try:
        fetch_jobs("data engineer")
    except requests.HTTPError:
        assert True
    else:
        assert False


def test_fetch_all_jobs_stops_on_empty_results(mocker):
    mocker.patch(
        "ingestion.api_client.fetch_jobs",
        return_value={"results": []}
    )

    jobs = fetch_all_jobs("data engineer", max_pages=5)

    assert jobs == []


def test_fetch_all_jobs_collects_multiple_pages(mocker):
    mocker.patch(
        "ingestion.api_client.fetch_jobs",
        side_effect=[
            {"results": [{"id": "1"}]},
            {"results": [{"id": "2"}]},
            {"results": []},
        ]
    )

    jobs = fetch_all_jobs("data engineer", max_pages=5)

    assert len(jobs) == 2


def test_fetch_jobs_missing_env_vars(mocker):
    mocker.patch("ingestion.api_client.APP_ID", None)

    try:
        fetch_jobs("data engineer")
    except EnvironmentError:
        assert True
    else:
        assert False