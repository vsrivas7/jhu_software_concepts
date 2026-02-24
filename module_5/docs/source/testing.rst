Testing Guide
=============

Running the Test Suite
----------------------

Run the full suite with coverage::

    pytest module_4/tests

Run by marker::

    pytest -m "web or buttons or analysis or db or integration"

Test Markers
------------

.. list-table::
   :widths: 20 60
   :header-rows: 1

   * - Marker
     - Description
   * - ``web``
     - Flask route and page rendering tests
   * - ``buttons``
     - Pull Data and Update Analysis endpoint tests
   * - ``analysis``
     - Formatting and rounding of analysis output
   * - ``db``
     - Database schema, inserts, and selects
   * - ``integration``
     - End-to-end pipeline tests

UI Selectors
------------

The following ``data-testid`` attributes are available for UI tests:

- ``data-testid="pull-data-btn"`` — Pull Data button
- ``data-testid="update-analysis-btn"`` — Update Analysis button

Test Doubles
------------

All tests use dependency injection via ``create_app()`` to pass fake
scraper, loader, and query functions. No tests hit the live network
or require a real database connection.