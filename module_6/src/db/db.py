"""
Shared database connection helper.
Centralises get_connection() to avoid duplication across modules.
"""

import os

import psycopg


def get_connection():
    """Return a psycopg connection using environment variables."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg.connect(database_url)  # pylint: disable=no-member
    return psycopg.connect(  # pylint: disable=no-member
        dbname=os.getenv("DB_NAME", "gradcafe"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASSWORD", ""),
    )
