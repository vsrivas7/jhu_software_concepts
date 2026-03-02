"""
Shared database connection helper for the web app.
"""
import os
import psycopg

def get_connection():
    """Return a psycopg connection using DATABASE_URL."""
    return psycopg.connect(os.environ.get("DATABASE_URL", ""))
