Setup & Overview
================

Grad Cafe Analytics is a data pipeline and web analytics service for graduate
school admissions data scraped from GradCafe. It scrapes applicant data, loads
it into PostgreSQL, and serves a Flask-based analysis page.

Environment Variables
---------------------

.. list-table::
   :widths: 25 50 10
   :header-rows: 1

   * - Variable
     - Description
     - Required
   * - DATABASE_URL
     - PostgreSQL connection string
     - Yes

Installation
------------

1. Clone the repo::

    git clone git@github.com:vsrivas7/jhu_software_concepts.git
    cd jhu_software_concepts/module_4

2. Install dependencies::

    pip install -r requirements.txt

3. Create a `.env` file::

    DATABASE_URL=postgresql://postgres:password@localhost:5432/gradcafe

Running the App
---------------

::

    flask --app src/flask_app run

Then open http://localhost:5000/analysis in your browser.

Running Tests
-------------

::

    pytest module_4/tests