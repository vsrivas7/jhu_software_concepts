import pytest
from src.load_data import load_rows


@pytest.mark.db
def test_load_rows_inserts(monkeypatch):
    fake_rows = [
        {
            "university": "Johns Hopkins",
            "program": "Computer Science",
            "degree": "MS",
            "decision": "Accepted",
            "season": "Fall 2026",
            "applicant_status": "International",
            "gpa": 3.9,
            "added_on": "2024-01-01",
            "result_id": "abc123",
            "page_scraped": 1
        }
    ]

    executed = {"count": 0}

    class FakeCursor:
        def execute(self, *args, **kwargs):
            executed["count"] += 1

        def close(self):
            pass

    class FakeConn:
        def cursor(self):
            return FakeCursor()

        def commit(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr("src.load_data.psycopg.connect", lambda *args, **kwargs: FakeConn())

    result = load_rows(fake_rows)

    assert result == 1
    assert executed["count"] == 1


@pytest.mark.db
def test_load_rows_empty():
    result = load_rows([])
    assert result == 0


@pytest.mark.db
def test_load_rows_multiple(monkeypatch):
    fake_rows = [
        {"university": "MIT", "program": "CS", "degree": "MS", "decision": "Accepted",
         "season": "Fall 2026", "applicant_status": "Domestic", "gpa": 3.8,
         "added_on": "2024-01-01", "result_id": "id1", "page_scraped": 1},
        {"university": "Stanford", "program": "CS", "degree": "PhD", "decision": "Rejected",
         "season": "Fall 2026", "applicant_status": "International", "gpa": 3.9,
         "added_on": "2024-01-02", "result_id": "id2", "page_scraped": 1},
    ]

    class FakeCursor:
        def execute(self, *args, **kwargs):
            pass

        def close(self):
            pass

    class FakeConn:
        def cursor(self):
            return FakeCursor()

        def commit(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr("src.load_data.psycopg.connect", lambda *args, **kwargs: FakeConn())

    result = load_rows(fake_rows)
    assert result == 2