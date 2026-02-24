Architecture
============

The system is composed of three layers:

Web Layer
---------

Built with Flask. Serves the Analysis page at ``/analysis`` and exposes two
POST endpoints: ``/pull-data`` and ``/update-analysis``. Uses a busy-state
flag to prevent concurrent operations.

ETL Layer
---------

``scrape.py`` scrapes applicant data from GradCafe. ``load_data.py`` cleans
and inserts rows into PostgreSQL using ``ON CONFLICT DO NOTHING`` to ensure
idempotency.

Database Layer
--------------

PostgreSQL stores applicant records in the ``applicants`` table. ``query_data.py``
queries the database and returns a dictionary of analysis results for display
on the Flask page.