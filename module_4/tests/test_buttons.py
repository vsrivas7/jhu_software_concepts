import pytest
from src.flask_app import create_app


@pytest.mark.buttons
def test_pull_data_success():
    fake_rows = [{"university": "Test U"}]

    def fake_scraper():
        return fake_rows

    called = {"loader_called": False}

    def fake_loader(rows):
        called["loader_called"] = True
        assert rows == fake_rows

    app = create_app(
        {"TESTING": True},
        scraper=fake_scraper,
        loader=fake_loader
    )

    client = app.test_client()
    response = client.post("/pull-data")

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert called["loader_called"] is True


@pytest.mark.buttons
def test_update_analysis_success(monkeypatch):
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.post("/update-analysis")

    assert response.status_code == 200
    assert response.json["ok"] is True


@pytest.mark.buttons
def test_busy_state_blocks_pull():
    app = create_app({"TESTING": True})
    app.config["BUSY"] = True
    client = app.test_client()

    response = client.post("/pull-data")

    assert response.status_code == 409
    assert response.json["busy"] is True


@pytest.mark.buttons
def test_busy_state_blocks_update():
    app = create_app({"TESTING": True})
    app.config["BUSY"] = True
    client = app.test_client()

    response = client.post("/update-analysis")

    assert response.status_code == 409
    assert response.json["busy"] is True

@pytest.mark.buttons
def test_pull_data_error_path(monkeypatch):
    def fake_scraper():
        raise Exception("Scraper failed")

    app = create_app(
        {"TESTING": True},
        scraper=fake_scraper
    )

    client = app.test_client()
    response = client.post("/pull-data")

    assert response.status_code == 500
    assert response.json["ok"] is False


@pytest.mark.buttons
def test_update_analysis_error_path(monkeypatch):
    def fake_query():
        raise Exception("Query failed")

    app = create_app(
        {"TESTING": True},
        query_fn=fake_query
    )

    client = app.test_client()
    response = client.post("/update-analysis")

    assert response.status_code == 500
    assert response.json["ok"] is False
