"""Module for querying data from the database."""

# pylint: disable=no-member

from typing import List, Tuple
from src.db import get_connection
from src.security import clamp_limit


def fetch_all_users(limit: int = 25) -> List[Tuple]:
    """Fetch users with enforced limit."""
    safe_limit = clamp_limit(limit)

    conn = get_connection()
    cur = conn.cursor()

    try:
        stmt = "SELECT * FROM users LIMIT %s;"
        cur.execute(stmt, (safe_limit,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def compute_analysis():
    """Compute analysis metrics with enforced LIMIT."""

    conn = get_connection()
    cur = conn.cursor()

    # Query 1
    stmt1 = """
        SELECT COUNT(*)
        FROM applicants
        WHERE term ILIKE '%fall%' AND term ILIKE '%2026%'
        LIMIT 1;
    """
    cur.execute(stmt1)
    fall_2026 = cur.fetchone()[0] or 0

    # Query 2
    stmt2 = """
        SELECT ROUND(
            100.0 * SUM(
                CASE WHEN us_or_international NOT IN ('American','Other')
                     AND us_or_international IS NOT NULL
                THEN 1 ELSE 0 END
            ) / NULLIF(COUNT(*), 0),
        2)
        FROM applicants
        LIMIT 1;
    """
    cur.execute(stmt2)
    intl_pct = cur.fetchone()[0]
    intl_pct = f"{float(intl_pct or 0):.2f}%"

    cur.close()
    conn.close()

    return {
        "Fall 2026 Applicants": fall_2026,
        "International %": intl_pct,
    }
