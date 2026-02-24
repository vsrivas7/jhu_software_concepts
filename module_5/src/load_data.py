"""Module for loading data into the database."""

# pylint: disable=no-member

from src.db import get_connection


def insert_user(username: str, email: str) -> None:
    """Insert a user into the database."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        stmt = "INSERT INTO users (username, email) VALUES (%s, %s);"
        cur.execute(stmt, (username, email))
        conn.commit()
    finally:
        cur.close()
        conn.close()


def load_rows(rows):
    """Insert rows into database."""
    if not rows:
        return 0

    conn = get_connection()
    cur = conn.cursor()

    stmt = """
        INSERT INTO applicants (
            university,
            program,
            degree,
            decision,
            season,
            applicant_status,
            gpa,
            added_on,
            result_id,
            page_scraped
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (result_id) DO NOTHING
    """

    inserted = 0

    for row in rows:
        cur.execute(stmt, (
            row.get("university"),
            row.get("program"),
            row.get("degree"),
            row.get("decision"),
            row.get("season"),
            row.get("applicant_status"),
            row.get("gpa"),
            row.get("added_on"),
            row.get("result_id"),
            row.get("page_scraped"),
        ))
        inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    return inserted
