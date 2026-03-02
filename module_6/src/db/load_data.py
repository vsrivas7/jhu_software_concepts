"""
Database loader for the GradCafe Flask application.
Inserts scraped rows using parameterised psycopg queries.
"""
import json
import os
from typing import Dict, List

import psycopg
from psycopg import sql

MAX_ROWS = 1000


def get_connection():
    """Return a psycopg connection using DATABASE_URL."""
    return psycopg.connect(os.environ["DATABASE_URL"])


def init_schema(conn):
    """Create tables if they do not exist."""
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS applicants (
            id              SERIAL PRIMARY KEY,
            university      TEXT,
            program         TEXT,
            degree          TEXT,
            decision        TEXT,
            season          TEXT,
            applicant_status TEXT,
            gpa             TEXT,
            added_on        TEXT,
            result_id       TEXT UNIQUE,
            page_scraped    INTEGER,
            us_or_international TEXT,
            term            TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ingestion_watermarks (
            source      TEXT PRIMARY KEY,
            last_seen   TEXT,
            updated_at  TIMESTAMPTZ DEFAULT now()
        )
    """)
    conn.commit()
    cur.close()


def load_rows(rows: List[Dict]) -> int:
    """Insert rows into the applicants table."""
    if not rows:
        return 0
    rows = rows[:MAX_ROWS]
    stmt = sql.SQL(
        "INSERT INTO {table} ("
        "university, program, degree, decision, season, "
        "applicant_status, gpa, added_on, result_id, page_scraped"
        ") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
        "ON CONFLICT (result_id) DO NOTHING"
    ).format(table=sql.Identifier("applicants"))

    conn = get_connection()
    cur = conn.cursor()
    inserted = 0
    for row in rows:
        cur.execute(stmt, (
            row.get("university"), row.get("program"), row.get("degree"),
            row.get("decision"), row.get("season"), row.get("applicant_status"),
            row.get("gpa"), row.get("added_on"), row.get("result_id"),
            row.get("page_scraped"),
        ))
        inserted += 1
    conn.commit()
    cur.close()
    conn.close()
    return inserted


def load_from_json(path: str) -> int:
    """Load applicant data from a JSON file into the database."""
    with open(path, "r", encoding="utf-8") as fh:
        rows = json.load(fh)
    conn = get_connection()
    init_schema(conn)
    conn.close()
    return load_rows(rows)


if __name__ == "__main__":
    json_path = os.getenv("DATA_PATH", "/data/applicant_data.json")
    total = load_from_json(json_path)
    print(f"Loaded {total} rows")
