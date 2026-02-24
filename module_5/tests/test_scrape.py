import pytest
import requests
import runpy
from unittest.mock import mock_open
from src.scrape import GradCafeScraper, scrape_data


# -----------------------------
# Fake HTTP Response
# -----------------------------
class FakeResponse:
    def __init__(self, content, status_code=200):
        self.content = content.encode("utf-8")
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.RequestException("HTTP error")


# -----------------------------
# scrape_page parsing success
# -----------------------------
@pytest.mark.db
def test_scrape_page_parses_rows(monkeypatch):
    fake_html = """
    <html>
        <table>
            <tr>
                <th>School</th>
                <th>Program</th>
                <th>Date</th>
                <th>Decision</th>
            </tr>
            <tr>
                <td>Test University</td>
                <td>Computer Science\nMS</td>
                <td>January 1, 2026</td>
                <td>Accepted|Fall 2026|American|GPA 3.8</td>
            </tr>
        </table>
    </html>
    """

    monkeypatch.setattr(
        "src.scrape.requests.get",
        lambda *a, **k: FakeResponse(fake_html)
    )

    scraper = GradCafeScraper()
    results = scraper.scrape_page(page_num=1)

    assert len(results) == 1
    row = results[0]

    assert row["university"] == "Test University"
    assert row["program"] == "Computer Science"
    assert row["degree"] == "MS"
    assert row["decision"] == "Accepted"
    assert row["season"] == "Fall 2026"
    assert row["applicant_status"] == "American"
    assert row["gpa"] == "3.8"


# -----------------------------
# HTTP error branch
# -----------------------------
@pytest.mark.db
def test_scrape_page_http_error(monkeypatch):
    monkeypatch.setattr(
        "src.scrape.requests.get",
        lambda *a, **k: (_ for _ in ()).throw(requests.RequestException())
    )

    scraper = GradCafeScraper()
    results = scraper.scrape_page(page_num=1)

    assert results == []


# -----------------------------
# No table branch
# -----------------------------
@pytest.mark.db
def test_scrape_page_no_table(monkeypatch):
    fake_html = "<html><body>No table here</body></html>"

    monkeypatch.setattr(
        "src.scrape.requests.get",
        lambda *a, **k: FakeResponse(fake_html)
    )

    scraper = GradCafeScraper()
    results = scraper.scrape_page(page_num=1)

    assert results == []


# -----------------------------
# Row parsing exception branch
# -----------------------------
@pytest.mark.db
def test_scrape_page_row_parse_exception(monkeypatch):
    fake_html = """
    <html>
        <table>
            <tr><th>School</th></tr>
            <tr><td>Broken Row</td></tr>
        </table>
    </html>
    """

    monkeypatch.setattr(
        "src.scrape.requests.get",
        lambda *a, **k: FakeResponse(fake_html)
    )

    scraper = GradCafeScraper()
    results = scraper.scrape_page(page_num=1)

    assert results == []


# -----------------------------
# scrape_dataset accumulation
# -----------------------------
@pytest.mark.db
def test_scrape_dataset_accumulates(monkeypatch):
    scraper = GradCafeScraper()

    monkeypatch.setattr(
        scraper,
        "scrape_page",
        lambda page_num=1, params=None: [{"result_id": str(page_num)}]
    )

    monkeypatch.setattr("builtins.open", mock_open())
    monkeypatch.setattr("src.scrape.time.sleep", lambda x: None)

    results = scraper.scrape_dataset(num_pages=3, output_file="test.json", delay=0)

    assert len(results) == 3


# -----------------------------
# scrape_dataset empty branch
# -----------------------------
@pytest.mark.db
def test_scrape_dataset_empty_page(monkeypatch):
    scraper = GradCafeScraper()

    monkeypatch.setattr(scraper, "scrape_page", lambda *a, **k: [])
    monkeypatch.setattr("builtins.open", mock_open())
    monkeypatch.setattr("src.scrape.time.sleep", lambda x: None)

    results = scraper.scrape_dataset(num_pages=1, output_file="test.json", delay=0)

    assert results == []


# -----------------------------
# sleep(delay) branch coverage
# -----------------------------
@pytest.mark.db
def test_scrape_dataset_sleep_branch(monkeypatch):
    scraper = GradCafeScraper()

    monkeypatch.setattr(scraper, "scrape_page", lambda *a, **k: [])

    sleep_called = {"called": False}

    def fake_sleep(x):
        sleep_called["called"] = True

    monkeypatch.setattr("src.scrape.time.sleep", fake_sleep)
    monkeypatch.setattr("builtins.open", mock_open())

    scraper.scrape_dataset(num_pages=2, output_file="test.json", delay=1)

    assert sleep_called["called"] is True


# -----------------------------
# scrape_data wrapper coverage
# -----------------------------
@pytest.mark.db
def test_scrape_data_wrapper(monkeypatch):
    monkeypatch.setattr(
        "src.scrape.GradCafeScraper.scrape_dataset",
        lambda self, num_pages=1: [{"wrapped": True}]
    )

    result = scrape_data()

    assert result == [{"wrapped": True}]


# -----------------------------
# __main__ block coverage
# -----------------------------
@pytest.mark.db
def test_main_block_exec(monkeypatch):
    monkeypatch.setattr(
        "src.scrape.GradCafeScraper.scrape_dataset",
        lambda self, num_pages=1: []
    )

    runpy.run_module("src.scrape", run_name="__main__")


# -----------------------------
# Force inner row exception branch (lines 97-98)
# -----------------------------
@pytest.mark.db
def test_scrape_page_forced_inner_exception(monkeypatch):
    fake_html = """
    <html>
        <table>
            <tr>
                <th>School</th>
                <th>Program</th>
                <th>Date</th>
                <th>Decision</th>
            </tr>
            <tr>
                <td>Test University</td>
                <td>Computer Science</td>
                <td>January 1, 2026</td>
                <td>Accepted</td>
            </tr>
        </table>
    </html>
    """

    monkeypatch.setattr(
        "src.scrape.requests.get",
        lambda *a, **k: FakeResponse(fake_html)
    )

    def broken_get_text(*args, **kwargs):
        raise ValueError("Forced parsing error")

    from bs4.element import Tag
    monkeypatch.setattr(Tag, "get_text", broken_get_text)

    scraper = GradCafeScraper()
    results = scraper.scrape_page(page_num=1)

    assert results == []
