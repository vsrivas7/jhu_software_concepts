"""
Database loader for the GradCafe Flask application.
Inserts scraped rows using parameterised psycopg queries — no raw string SQL.
"""

from typing import Dict, List

from psycopg import sql

from .db import get_connection


# Maximum rows allowed per load call (prevents runaway inserts)
MAX_ROWS = 1000


def load_rows(rows: List[Dict]) -> int:
    """
    Insert rows into the applicants table.
    Used by the Flask /pull-data endpoint.

    SQL statement is constructed via sql.SQL + sql.Identifier so the table
    name is safely quoted. All values go through %s parameter binding —
    never interpolated into SQL text.
    """
    if not rows:
        return 0

    # Clamp to at most MAX_ROWS to enforce a reasonable limit
    rows = rows[:MAX_ROWS]

    stmt = sql.SQL(
        "INSERT INTO {table} ("
        "university, program, degree, decision, season, "
        "applicant_status, gpa, added_on, result_id, page_scraped"
        ") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
        "ON CONFLICT (result_id) DO NOTHING"
    ).format(table=sql.Identifier("applicants"))

    conn = get_connection()
    cur = conn.cursor()  # pylint: disable=no-member
    inserted = 0

    for row in rows:
        cur.execute(
            stmt,
            (
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
            ),
        )
        inserted += 1

    conn.commit()  # pylint: disable=no-member
    cur.close()
    conn.close()  # pylint: disable=no-member

    return inserted
