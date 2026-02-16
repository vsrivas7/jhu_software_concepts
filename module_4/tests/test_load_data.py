import pytest
from src import load_data


class FakeCursor:
    def __init__(self):
        self.executed = 0

    def execute(self, sql, params):
        self.executed += 1

    def close(self):
        pass


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()
        self.committed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def close(self):
        pass


@pytest.mark.db
def test_load_rows_empty():
    result = load_data.load_rows([])
    assert result == 0


@pytest.mark.db
def test_load_rows_inserts(monkeypatch):
    fake_conn = FakeConnection()

    monkeypatch.setattr(load_data, "get_connection", lambda: fake_conn)

    rows = [
        {
            "university": "U1",
            "program": "P1",
            "degree": "MS",
            "decision": "Accept",
            "season": "Fall",
            "applicant_status": "International",
            "gpa": "3.5",
            "added_on": "2025-01-01",
            "result_id": "123",
            "page_scraped": 1
        },
        {
            "university": "U2",
            "program": "P2",
            "degree": "PhD",
            "decision": "Reject",
            "season": "Fall",
            "applicant_status": "American",
            "gpa": "3.8",
            "added_on": "2025-01-02",
            "result_id": "124",
            "page_scraped": 1
        }
    ]

    inserted = load_data.load_rows(rows)

    assert inserted == 2
    assert fake_conn.cursor_obj.executed == 2
    assert fake_conn.committed is True

@pytest.mark.db
def test_get_connection_with_database_url(monkeypatch):
    def fake_connect(url=None, **kwargs):
        return "url_conn"

    monkeypatch.setenv("DATABASE_URL", "postgres://fake")
    monkeypatch.setattr(load_data.psycopg, "connect", fake_connect)

    conn = load_data.get_connection()

    assert conn == "url_conn"


@pytest.mark.db
def test_get_connection_without_database_url(monkeypatch):
    def fake_connect(*args, **kwargs):
        return "default_conn"

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(load_data.psycopg, "connect", fake_connect)

    conn = load_data.get_connection()

    assert conn == "default_conn"
