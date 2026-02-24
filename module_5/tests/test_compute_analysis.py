import pytest
from src import query_data


class FakeCursor:
    def __init__(self, results):
        self.results = results
        self.call_count = 0

    def execute(self, sql):
        pass

    def fetchone(self):
        result = self.results[self.call_count]
        self.call_count += 1
        return (result,)


class FakeConnection:
    def __init__(self, results):
        self.results = results

    def cursor(self):
        return FakeCursor(self.results)

    def close(self):
        pass


@pytest.mark.analysis
def test_compute_analysis_normal(monkeypatch):
    fake_conn = FakeConnection([10, 25.5])
    monkeypatch.setattr(query_data, "get_connection", lambda: fake_conn)

    result = query_data.compute_analysis()

    assert result["Fall 2026 Applicants"] == 10
    assert result["International %"] == "25.50%"


@pytest.mark.analysis
def test_compute_analysis_handles_none(monkeypatch):
    fake_conn = FakeConnection([None, None])
    monkeypatch.setattr(query_data, "get_connection", lambda: fake_conn)

    result = query_data.compute_analysis()

    assert result["Fall 2026 Applicants"] == 0
    assert result["International %"] == "0.00%"
