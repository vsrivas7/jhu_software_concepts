import pytest
from src.flask_app import create_app


@pytest.mark.web
def test_app_factory_creates_app():
    app = create_app({"TESTING": True})
    assert app is not None


@pytest.mark.web
def test_analysis_page_loads():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/analysis")

    assert response.status_code == 200


@pytest.mark.web
def test_analysis_page_contains_required_elements():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/analysis")
    html = response.data.decode()

    assert "Analysis" in html
    assert 'data-testid="pull-data-btn"' in html
    assert 'data-testid="update-analysis-btn"' in html
    assert "Answer:" in html


@pytest.mark.web
def test_analysis_handles_none_query():
    """
    Forces the fallback branch:
    data = app.query_fn() or {}
    """
    def fake_query():
        return None

    app = create_app(
        {"TESTING": True},
        query_fn=fake_query
    )

    client = app.test_client()
    response = client.get("/analysis")

    assert response.status_code == 200
    html = response.data.decode()
    assert "Analysis" in html
