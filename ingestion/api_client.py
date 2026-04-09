import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search"

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

# Job titles to search for — focused on DA/DS roles
TARGET_ROLES = [
    "data analyst",
    "data scientist",
    "business analyst",
    "data engineer",
    "machine learning engineer",
    "analytics engineer",
]

RESULTS_PER_PAGE = 50  # Adzuna max per request


def fetch_jobs(role: str, page: int = 1) -> dict:
    """Fetch one page of job listings for a given role."""
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": RESULTS_PER_PAGE,
        "what": role,
        "content-type": "application/json",
    }
    url = f"{BASE_URL}/{page}"
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_all_jobs(role: str, max_pages: int = 5) -> list[dict]:
    """Fetch multiple pages of listings for a role, respecting rate limits."""
    all_jobs = []
    for page in range(1, max_pages + 1):
        data = fetch_jobs(role, page)
        results = data.get("results", [])
        if not results:
            break
        all_jobs.extend(results)
        print(f"  [{role}] page {page}: {len(results)} jobs fetched")
        time.sleep(0.5)  # be polite to the API
    return all_jobs


def fetch_all_roles(max_pages_per_role: int = 5) -> list[dict]:
    """Fetch jobs for all target roles and tag each with its search role."""
    all_jobs = []
    for role in TARGET_ROLES:
        print(f"Fetching: {role}")
        jobs = fetch_all_jobs(role, max_pages=max_pages_per_role)
        for job in jobs:
            job["search_role"] = role  # track which query returned this listing
        all_jobs.extend(jobs)
        time.sleep(1)
    print(f"\nTotal jobs fetched: {len(all_jobs)}")
    return all_jobs


if __name__ == "__main__":
    jobs = fetch_all_roles(max_pages_per_role=2)
    print(f"Sample job keys: {list(jobs[0].keys()) if jobs else 'no results'}")
