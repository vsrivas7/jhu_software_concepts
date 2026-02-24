"""
Pytest test suite for the GradCafe Flask application.
Uses dependency injection so no real DB or network calls are made.
"""

import pytest

from src.flask_app import create_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _mock_scraper():
    """Return a minimal fake scraped dataset."""
    return [
        {
            "university": "MIT",
            "program": "Computer Science",
            "degree": "PhD",
            "decision": "Accepted",
            "season": "Fall 2026",
            "applicant_status": "International",
            "gpa": "3.9",
            "added_on": "2024-01-01",
            "result_id": "test-001",
            "page_scraped": 1,
        }
    ]


def _mock_loader(rows):
    """Fake loader — just count rows without touching the DB."""
    return len(rows)


def _mock_query_fn():
    """Return fake analysis data."""
    return {"Fall 2026 Applicants": 42, "International %": "55.00%"}


@pytest.fixture
def client():
    """Create a test Flask client with injected mocks."""
    app = create_app(
        scraper=_mock_scraper,
        loader=_mock_loader,
        query_fn=_mock_query_fn,
    )
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Tests — /analysis
# ---------------------------------------------------------------------------

class TestAnalysis:
    """Tests for the /analysis endpoint."""

    def test_analysis_returns_200(self, client):
        """GET /analysis should return HTTP 200."""
        response = client.get("/analysis")
        assert response.status_code == 200

    def test_analysis_contains_key(self, client):
        """Response body should include expected analysis keys."""
        response = client.get("/analysis")
        assert b"Fall 2026 Applicants" in response.data

    def test_analysis_contains_value(self, client):
        """Response body should include the mocked value."""
        response = client.get("/analysis")
        assert b"42" in response.data

    def test_analysis_contains_buttons(self, client):
        """Page should include the required data-testid buttons."""
        response = client.get("/analysis")
        assert b"pull-data-btn" in response.data
        assert b"update-analysis-btn" in response.data


# ---------------------------------------------------------------------------
# Tests — /pull-data
# ---------------------------------------------------------------------------

class TestPullData:
    """Tests for the /pull-data endpoint."""

    def test_pull_data_returns_ok(self, client):
        """POST /pull-data should return {ok: true} and HTTP 200."""
        response = client.post("/pull-data")
        assert response.status_code == 200
        assert response.get_json() == {"ok": True}

    def test_pull_data_busy_returns_409(self, client):
        """When BUSY flag is set, /pull-data should return HTTP 409."""
        with client.application.test_request_context():
            client.application.config["BUSY"] = True
        response = client.post("/pull-data")
        assert response.status_code == 409

    def test_pull_data_error_returns_500(self):
        """When scraper raises, /pull-data should return HTTP 500."""
        def _bad_scraper():
            raise RuntimeError("scraper failed")

        app = create_app(scraper=_bad_scraper, loader=_mock_loader, query_fn=_mock_query_fn)
        app.config["TESTING"] = True
        with app.test_client() as bad_client:
            response = bad_client.post("/pull-data")
        assert response.status_code == 500
        assert response.get_json() == {"ok": False}


# ---------------------------------------------------------------------------
# Tests — /update-analysis
# ---------------------------------------------------------------------------

class TestUpdateAnalysis:
    """Tests for the /update-analysis endpoint."""

    def test_update_analysis_returns_ok(self, client):
        """POST /update-analysis should return {ok: true} and HTTP 200."""
        response = client.post("/update-analysis")
        assert response.status_code == 200
        assert response.get_json() == {"ok": True}

    def test_update_analysis_busy_returns_409(self, client):
        """When BUSY flag is set, /update-analysis should return HTTP 409."""
        with client.application.test_request_context():
            client.application.config["BUSY"] = True
        response = client.post("/update-analysis")
        assert response.status_code == 409

    def test_update_analysis_error_returns_500(self):
        """When query_fn raises, /update-analysis should return HTTP 500."""
        def _bad_query():
            raise RuntimeError("query failed")

        app = create_app(scraper=_mock_scraper, loader=_mock_loader, query_fn=_bad_query)
        app.config["TESTING"] = True
        with app.test_client() as bad_client:
            response = bad_client.post("/update-analysis")
        assert response.status_code == 500
        assert response.get_json() == {"ok": False}
