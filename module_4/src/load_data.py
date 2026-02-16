import os
import psycopg


def get_connection():
    """Connect using DATABASE_URL if available"""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg.connect(database_url)
    return psycopg.connect(
        dbname="gradcafe",
        host="localhost",
        port=5432
    )


def load_rows(rows):
    """
    Insert rows into database.
    Used by Flask /pull-data endpoint.
    """
    if not rows:
        return 0

    conn = get_connection()
    cur = conn.cursor()

    sql = """
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
        cur.execute(sql, (
            row.get("university"),
            row.get("program"),
            row.get("degree"),
            row.get("decision"),
            row.get("season"),
            row.get("applicant_status"),
            row.get("gpa"),
            row.get("added_on"),
            row.get("result_id"),
            row.get("page_scraped")
        ))
        inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    return inserted
