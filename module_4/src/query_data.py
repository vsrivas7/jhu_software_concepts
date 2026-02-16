import os
import psycopg


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg.connect(database_url)
    return psycopg.connect(
        dbname="gradcafe",
        host="localhost",
        port=5432
    )


def compute_analysis():
    """
    Used by Flask /analysis endpoint.
    Returns dictionary for template rendering.
    """

    conn = get_connection()
    cur = conn.cursor()

    # 1. Fall 2026 count
    cur.execute("""
        SELECT COUNT(*)
        FROM applicants
        WHERE term ILIKE '%fall%' AND term ILIKE '%2026%';
    """)
    fall_2026 = cur.fetchone()[0] or 0

    # 2. International %
    cur.execute("""
        SELECT ROUND(
            100.0 * SUM(
                CASE WHEN us_or_international NOT IN ('American','Other')
                     AND us_or_international IS NOT NULL
                THEN 1 ELSE 0 END
            ) / NULLIF(COUNT(*), 0),
        2)
        FROM applicants;
    """)
    intl_pct = cur.fetchone()[0]
    intl_pct = f"{float(intl_pct or 0):.2f}%"

    conn.close()

    return {
        "Fall 2026 Applicants": fall_2026,
        "International %": intl_pct
    }
