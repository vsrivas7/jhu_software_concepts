import pytest
from src import query_data


@pytest.mark.analysis
def test_get_connection_with_database_url(monkeypatch):
    def fake_connect(url=None, **kwargs):
        return "url_connection"

    monkeypatch.setenv("DATABASE_URL", "postgres://fake")
    monkeypatch.setattr(query_data.psycopg, "connect", fake_connect)

    conn = query_data.get_connection()

    assert conn == "url_connection"


@pytest.mark.analysis
def test_get_connection_without_database_url(monkeypatch):
    def fake_connect(*args, **kwargs):
        return "default_connection"

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(query_data.psycopg, "connect", fake_connect)

    conn = query_data.get_connection()

    assert conn == "default_connection"
