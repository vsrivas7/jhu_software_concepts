import json
import psycopg
from datetime import datetime

DB_NAME = "gradcafe"
DB_USER = None
DB_HOST = "localhost"
DB_PORT = 5432

JSON_FILE =  "llm_extended_applicant_data.json"



def normalize(value):
    """Convert empty strings to None."""
    if value == "" or value is None:
        return None
    return value


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%B %d, %Y")
    except:
        return None


def load_data():
    print("Connecting to PostgreSQL...")
    conn = psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()

    print("Loading JSON file:", JSON_FILE)
    with open(JSON_FILE, "r") as f:
        data = json.load(f)["applicants"]

    print("Clearing table...")
    cur.execute("DELETE FROM applicants;")

    sql = """
        INSERT INTO applicants (
            program, comments, date_added, url, status, term,
            us_or_international, gpa, gre, gre_v, gre_aw,
            degree, llm_generated_program, llm_generated_university
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    print("Inserting rows...")

    for row in data:
        cur.execute(sql, (
            normalize(row.get("program_name")),
            normalize(row.get("comments")),
            parse_date(row.get("date_added")),
            normalize(row.get("entry_url")),
            normalize(row.get("status")),
            normalize(row.get("term_start")),
            normalize(row.get("student_type")),
            normalize(row.get("gpa")),
            normalize(row.get("gre_total")),
            normalize(row.get("gre_verbal")),
            normalize(row.get("gre_aw")),
            normalize(row.get("degree_type")),
            normalize(row.get("cleaned_program")),
            normalize(row.get("cleaned_university"))
        ))

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Data successfully loaded into PostgreSQL!")


if __name__ == "__main__":
    load_data()
