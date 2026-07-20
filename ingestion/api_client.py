import logging
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search"

TARGET_ROLES = [
    "data analyst",
    "data scientist",
    "business analyst",
    "data engineer",
    "machine learning engineer",
    "analytics engineer",
]

RESULTS_PER_PAGE = 50  # Adzuna max per request


def fetch_jobs(
    role: str,
    page: int = 1,
    *,
    app_id: str | None = None,
    app_key: str | None = None,
) -> dict:
    """Fetch one page of job listings for a given role."""
    resolved_app_id = app_id if app_id is not None else os.getenv("ADZUNA_APP_ID")
    resolved_app_key = app_key if app_key is not None else os.getenv("ADZUNA_APP_KEY")

    if not resolved_app_id or not resolved_app_key:
        raise EnvironmentError(
            "ADZUNA_APP_ID and ADZUNA_APP_KEY must be set in the environment "
            "or passed explicitly."
        )

    params = {
        "app_id": resolved_app_id,
        "app_key": resolved_app_key,
        "results_per_page": RESULTS_PER_PAGE,
        "what": role,
        "content-type": "application/json",
    }
    url = f"{BASE_URL}/{page}"

    logger.debug("GET %s (role=%r, page=%d)", url, role, page)
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_all_jobs(
    role: str,
    max_pages: int = 5,
    *,
    app_id: str | None = None,
    app_key: str | None = None,
) -> list[dict]:
    """Fetch multiple pages of listings for a role, respecting rate limits."""
    all_jobs = []

    for page in range(1, max_pages + 1):
        try:
            data = fetch_jobs(
                role,
                page,
                app_id=app_id,
                app_key=app_key,
            )
        except requests.HTTPError as e:
            logger.error("HTTP error fetching role=%r page=%d: %s", role, page, e)
            break
        except requests.RequestException as e:
            logger.error("Request failed for role=%r page=%d: %s", role, page, e)
            break

        results = data.get("results", [])
        if not results:
            logger.debug("No results on page %d for role=%r — stopping early", page, role)
            break

        all_jobs.extend(results)
        logger.info("  [%s] page %d: %d jobs fetched", role, page, len(results))
        time.sleep(0.5)  # be polite to the API

    return all_jobs


def fetch_all_roles(
    max_pages_per_role: int = 5,
    *,
    app_id: str | None = None,
    app_key: str | None = None,
) -> list[dict]:
    """Fetch jobs for all target roles and tag each with its search role."""
    all_jobs = []

    for role in TARGET_ROLES:
        logger.info("Fetching role: %s", role)
        jobs = fetch_all_jobs(
            role,
            max_pages=max_pages_per_role,
            app_id=app_id,
            app_key=app_key,
        )
        for job in jobs:
            job["search_role"] = role
        all_jobs.extend(jobs)
        time.sleep(1)

    logger.info("Total jobs fetched across all roles: %d", len(all_jobs))
    return all_jobs


if __name__ == "__main__":
    from logger import setup_logging
    setup_logging()
    jobs = fetch_all_roles(max_pages_per_role=2)
    logger.info("Sample job keys: %s", list(jobs[0].keys()) if jobs else "no results")
