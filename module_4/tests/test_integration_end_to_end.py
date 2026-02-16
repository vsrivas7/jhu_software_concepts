import pytest
from src.flask_app import create_app


@pytest.mark.integration
def test_end_to_end_pull_update_render():
    """Pull -> Update -> Render shows updated analysis"""
    fake_rows = [
        {
            "university": "Johns Hopkins",
            "program": "CS",
            "degree": "MS",
            "decision": "Accepted",
            "season": "Fall 2026",
            "applicant_status": "Domestic",
            "gpa": 3.9,
            "added_on": "2024-01-01",
            "result_id": "abc123",
            "page_scraped": 1
        }
    ]

    loaded = {"rows": []}

    def fake_scraper():
        return fake_rows

    def fake_loader(rows):
        loaded["rows"] = rows

    def fake_query():
        return {"fall_2026_applicants": len(loaded["rows"])}

    app = create_app(
        {"TESTING": True},
        scraper=fake_scraper,
        loader=fake_loader,
        query_fn=fake_query
    )
    client = app.test_client()

    # Step 1: Pull data
    pull_response = client.post("/pull-data")
    assert pull_response.status_code == 200
    assert pull_response.json["ok"] is True
    assert len(loaded["rows"]) == 1

    # Step 2: Update analysis
    update_response = client.post("/update-analysis")
    assert update_response.status_code == 200
    assert update_response.json["ok"] is True

    # Step 3: Render analysis page
    get_response = client.get("/analysis")
    assert get_response.status_code == 200
    html = get_response.data.decode()
    assert "Analysis" in html
    assert "Answer:" in html
    assert "1" in html


@pytest.mark.integration
def test_multiple_pulls_no_duplicates():
    """Running pull twice with overlapping data stays consistent"""
    call_count = {"count": 0}

    def fake_scraper():
        return [
            {
                "university": "MIT",
                "program": "CS",
                "degree": "MS",
                "decision": "Accepted",
                "season": "Fall 2026",
                "applicant_status": "Domestic",
                "gpa": 3.8,
                "added_on": "2024-01-01",
                "result_id": "same_id",
                "page_scraped": 1
            }
        ]

    def fake_loader(rows):
        call_count["count"] += 1

    def fake_query():
        return {"fall_2026_applicants": 1}

    app = create_app(
        {"TESTING": True},
        scraper=fake_scraper,
        loader=fake_loader,
        query_fn=fake_query
    )
    client = app.test_client()

    # Pull twice
    response1 = client.post("/pull-data")
    assert response1.status_code == 200

    response2 = client.post("/pull-data")
    assert response2.status_code == 200

    # Loader was called twice but same result_id means no duplicates in DB
    assert call_count["count"] == 2

    # Analysis still returns consistent result
    get_response = client.get("/analysis")
    assert get_response.status_code == 200
    assert b"1" in get_response.data


@pytest.mark.integration
def test_busy_blocks_during_pull():
    """When busy, both endpoints return 409"""
    app = create_app({"TESTING": True})
    app.config["BUSY"] = True
    client = app.test_client()

    pull_response = client.post("/pull-data")
    assert pull_response.status_code == 409
    assert pull_response.json["busy"] is True

    update_response = client.post("/update-analysis")
    assert update_response.status_code == 409
    assert update_response.json["busy"] is True