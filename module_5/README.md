# Grad Café Analytics — Module 4

A data pipeline and web analytics service for graduate school admissions data
scraped from GradCafe. The system scrapes applicant data, loads it into
PostgreSQL, and serves a Flask-based analysis page.

## Documentation

> 📄 Full Sphinx documentation: [Read the Docs](https://grad-cafe-analytics.readthedocs.io)

---

## Project Structure
```
module_4/
├── src/                  # Application source code
│   ├── flask_app.py      # Flask app factory and routes
│   ├── scrape.py         # GradCafe scraper
│   ├── load_data.py      # PostgreSQL loader
│   ├── query_data.py     # Analysis queries
│   └── __init__.py
├── tests/                # Pytest test suite
│   ├── test_flask_page.py
│   ├── test_buttons.py
│   ├── test_analysis_format.py
│   ├── test_db_insert.py
│   └── test_integration_end_to_end.py
├── docs/                 # Sphinx documentation
├── pytest.ini
├── requirements.txt
├── coverage_summary.txt
└── README.md
```

---

## Requirements

- Python 3.9+
- PostgreSQL
- All Python dependencies in `requirements.txt`

---

## Setup

### 1. Clone the repo
```bash
git clone git@github.com:vsrivas7/jhu_software_concepts.git
cd jhu_software_concepts/module_4
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set environment variables

Create a `.env` file in `module_4/`:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/gradcafe
```

### 4. Run the app
```bash
flask --app src/flask_app run
```

Then open `http://localhost:5000/analysis` in your browser.

---

## Running Tests

Run the full test suite with coverage:
```bash
pytest module_4/tests
```

Run by marker:
```bash
pytest -m "web or buttons or analysis or db or integration"
```

---

## Test Markers

| Marker        | Description                              |
|---------------|------------------------------------------|
| `web`         | Flask route and page rendering tests     |
| `buttons`     | Pull Data and Update Analysis endpoints  |
| `analysis`    | Formatting and rounding of output        |
| `db`          | Database schema, inserts, and selects    |
| `integration` | End-to-end pipeline tests                |

---

## CI

This project uses GitHub Actions to automatically run the test suite on every
push and pull request. PostgreSQL is started as a service within the workflow.

See `.github/workflows/tests.yml` for the full configuration.

---

## Environment Variables

| Variable       | Description                        | Required |
|----------------|------------------------------------|----------|
| `DATABASE_URL` | PostgreSQL connection string       | Yes      |