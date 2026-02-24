"""
Query helpers for the GradCafe Flask application.
All SQL is constructed with psycopg sql composition — no raw string interpolation.
"""

from psycopg import sql

from .db import get_connection


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_LIMIT = 1
MAX_LIMIT = 100
DEFAULT_LIMIT = 50


def _clamp_limit(limit: int) -> int:
    """Clamp limit to the allowed range [MIN_LIMIT, MAX_LIMIT]."""
    return max(MIN_LIMIT, min(limit, MAX_LIMIT))


# ---------------------------------------------------------------------------
# Analysis queries
# ---------------------------------------------------------------------------

def compute_analysis(limit: int = DEFAULT_LIMIT) -> dict:
    """
    Used by Flask /analysis endpoint.
    Returns a dictionary for template rendering.

    All queries use safe psycopg SQL composition:
      - sql.SQL for statement structure
      - %s placeholders for all user-supplied values
      - sql.Identifier for dynamic identifiers (table/column names)
      - LIMIT is enforced and clamped on every query
    """
    safe_limit = _clamp_limit(limit)

    conn = get_connection()
    cur = conn.cursor()  # pylint: disable=no-member

    # ------------------------------------------------------------------
    # 1. Fall 2026 count
    #    Dynamic table name via sql.Identifier; values via %s params.
    # ------------------------------------------------------------------
    stmt_fall = sql.SQL(
        "SELECT COUNT(*) FROM {table} "
        "WHERE term ILIKE %s AND term ILIKE %s "
        "LIMIT %s"
    ).format(table=sql.Identifier("applicants"))

    cur.execute(stmt_fall, ("%fall%", "%2026%", safe_limit))
    row = cur.fetchone()
    fall_2026 = row[0] if row else 0

    # ------------------------------------------------------------------
    # 2. International applicant percentage
    #    Column names via sql.Identifier; values via %s params.
    # ------------------------------------------------------------------
    stmt_intl = sql.SQL(
        "SELECT ROUND("
        "  100.0 * SUM("
        "    CASE WHEN {col} NOT IN (%s, %s) AND {col} IS NOT NULL"
        "         THEN 1 ELSE 0 END"
        "  ) / NULLIF(COUNT(*), 0), 2"
        ") FROM {table} "
        "LIMIT %s"
    ).format(
        col=sql.Identifier("us_or_international"),
        table=sql.Identifier("applicants"),
    )

    cur.execute(stmt_intl, ("American", "Other", safe_limit))
    row = cur.fetchone()
    intl_pct = f"{float(row[0] or 0):.2f}%" if row else "0.00%"

    cur.close()
    conn.close()  # pylint: disable=no-member

    return {
        "Fall 2026 Applicants": fall_2026,
        "International %": intl_pct,
    }


def query_applicants(
    university: str = None,
    decision: str = None,
    limit: int = DEFAULT_LIMIT,
) -> list:
    """
    Return applicant rows filtered by optional university and/or decision.

    Demonstrates safe dynamic WHERE clause construction with sql.SQL,
    sql.Identifier, and parameterised values — no f-strings or concatenation.
    """
    safe_limit = _clamp_limit(limit)
    params = []

    conditions = []
    if university:
        conditions.append(
            sql.SQL("{col} ILIKE %s").format(col=sql.Identifier("university"))
        )
        params.append(f"%{university}%")

    if decision:
        conditions.append(
            sql.SQL("{col} ILIKE %s").format(col=sql.Identifier("decision"))
        )
        params.append(f"%{decision}%")

    where_clause = (
        sql.SQL(" WHERE ") + sql.SQL(" AND ").join(conditions)
        if conditions
        else sql.SQL("")
    )

    stmt = sql.SQL(
        "SELECT university, program, degree, decision, season, "
        "us_or_international, gpa, added_on "
        "FROM {table}{where} "
        "LIMIT %s"
    ).format(
        table=sql.Identifier("applicants"),
        where=where_clause,
    )

    params.append(safe_limit)

    conn = get_connection()
    cur = conn.cursor()  # pylint: disable=no-member
    cur.execute(stmt, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()  # pylint: disable=no-member

    return rows
