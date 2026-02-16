Module 3 – SQL, PostgreSQL, and Flask Assignment

This folder contains all files required for Module 3 of the JHU Software Concepts course.
The assignment loads Grad Café applicant data into a PostgreSQL database, runs SQL queries, and displays results in a Flask webpage.

Included Files

load_data.py — Loads cleaned Grad Café data into PostgreSQL

query_data.py — Runs required SQL queries and prints results

app.py — Flask app to display SQL outputs on a webpage

applicant_data.json — Input dataset

llm_extended_applicant_data.json — Cleaned dataset with LLM fields

templates/ — HTML template for Flask

limitations.pdf — Discussion of dataset limitations

module_2/ — Required scraper code from previous assignment

requirements.txt — Python dependencies

How to Run

Load data into PostgreSQL:

python load_data.py


Execute SQL queries:

python query_data.py


Run Flask app:

python app.py