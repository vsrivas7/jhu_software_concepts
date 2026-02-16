import pytest
import re
from src.flask_app import create_app


@pytest.mark.analysis
def test_analysis_returns_dict(monkeypatch):
    class FakeCursor:
        def execute(self, *args, **kwargs):
            pass

        def fetchone(self):
            return (10,)

        def close(self):
            pass

    class FakeConn:
        def cursor(self):
            return FakeCursor()

        def close(self):
            pass

    monkeypatch.setattr("src.query_data.psycopg.connect", lambda *args, **kwargs: FakeConn())

    from src.query_data import compute_analysis
    result = compute_analysis()

    assert isinstance(result, dict)
    assert "Fall 2026 Applicants" in result
    assert isinstance(result["Fall 2026 Applicants"], int)


@pytest.mark.analysis
def test_analysis_page_shows_answer_labels():
    def fake_query():
        return {"Fall 2026 Applicants": 42}

    app = create_app({"TESTING": True}, query_fn=fake_query)
    client = app.test_client()

    response = client.get("/analysis")
    html = response.data.decode()

    assert "Answer:" in html


@pytest.mark.analysis
def test_analysis_percentage_two_decimals():
    def fake_query():
        return {"acceptance_rate": "39.28%"}

    app = create_app({"TESTING": True}, query_fn=fake_query)
    client = app.test_client()

    response = client.get("/analysis")
    html = response.data.decode()

    percentages = re.findall(r"\d+\.\d+%", html)
    for p in percentages:
        decimal_part = p.split(".")[1].rstrip("%")
        assert len(decimal_part) == 2, f"Percentage {p} is not formatted to 2 decimals"


@pytest.mark.analysis
def test_analysis_empty_data_still_loads():
    def fake_query():
        return {}

    app = create_app({"TESTING": True}, query_fn=fake_query)
    client = app.test_client()

    response = client.get("/analysis")
    assert response.status_code == 200