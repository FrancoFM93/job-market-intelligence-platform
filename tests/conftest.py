from datetime import datetime

import pytest


@pytest.fixture
def sample_raw_job():
    return {
        "id": "123",
        "title": "Data Engineer",
        "company": {"display_name": "OpenAI"},
        "location": {
            "display_name": "Remote",
            "area": ["US", "California", "San Francisco"]
        },
        "description": "Build data pipelines.",
        "category": {"label": "IT Jobs"},
        "contract_type": "full_time",
        "contract_time": "permanent",
        "salary_min": 90000,
        "salary_max": 120000,
        "salary_is_predicted": "0",
        "redirect_url": "https://example.com/job",
        "search_role": "data engineer",
        "created": "2026-05-20T12:00:00Z",
    }