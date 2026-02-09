from flask import Flask, render_template, redirect, url_for
import psycopg
import subprocess
import threading

app = Flask(__name__)
scrape_running = False

DB_NAME = "gradcafe"
DB_USER = None
DB_HOST = "localhost"
DB_PORT = 5432


def get_results():
    conn = psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()
    results = {}

    # 1. Fall 2026 applicants
    cur.execute("""
        SELECT COUNT(*)
        FROM applicants
        WHERE term ILIKE '%fall%' AND term ILIKE '%2026%';
    """)
    results["fall_2026"] = cur.fetchone()[0]

    # 2. International %
    cur.execute("""
        SELECT ROUND(
            100.0 * SUM(
                CASE WHEN us_or_international NOT IN ('American','Other')
                     AND us_or_international IS NOT NULL
                THEN 1 ELSE 0 END
            ) / NULLIF(COUNT(*), 0), 2)
        FROM applicants;
    """)
    results["international_pct"] = cur.fetchone()[0]

    # 3. Average GPA/GRE
    cur.execute("""
        SELECT
            ROUND(AVG(gpa)::numeric, 2),
            ROUND(AVG(gre)::numeric, 2),
            ROUND(AVG(gre_v)::numeric, 2),
            ROUND(AVG(gre_aw)::numeric, 2)
        FROM applicants;
    """)
    results["averages"] = cur.fetchone()

    # 4. Avg GPA American Fall 2026
    cur.execute("""
        SELECT ROUND(AVG(gpa)::numeric, 2)
        FROM applicants
        WHERE us_or_international = 'American'
          AND term ILIKE '%fall%' AND term ILIKE '%2026%';
    """)
    results["american_gpa_2026"] = cur.fetchone()[0]

    # 5. Fall 2025 acceptance %
    cur.execute("""
        SELECT ROUND(
            100.0 * SUM(CASE WHEN status ILIKE '%accept%' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0), 2)
        FROM applicants
        WHERE term ILIKE '%fall%' AND term ILIKE '%2025%';
    """)
    results["fall_2025_accept_pct"] = cur.fetchone()[0]

    # 6. Avg GPA accepted Fall 2026
    cur.execute("""
        SELECT ROUND(AVG(gpa)::numeric, 2)
        FROM applicants
        WHERE term ILIKE '%fall%'
          AND term ILIKE '%2026%'
          AND status ILIKE '%accept%';
    """)
    results["accepted_gpa_2026"] = cur.fetchone()[0]

    # 7. JHU MS CS applicants
    cur.execute("""
        SELECT COUNT(*)
        FROM applicants
        WHERE llm_generated_university ILIKE '%johns hopkins%'
          AND degree ILIKE '%ms%'
          AND llm_generated_program ILIKE '%computer science%';
    """)
    results["jhu_ms_cs"] = cur.fetchone()[0]


    # --- ADD Q8 ---
    cur.execute("""
        SELECT COUNT(*)
        FROM applicants
        WHERE term ILIKE '%2026%'
          AND degree ILIKE '%phd%'
          AND program ILIKE '%computer%'
          AND status ILIKE '%accept%'
          AND (
                llm_generated_university ILIKE '%georgetown%' OR
                llm_generated_university ILIKE '%mit%' OR
                llm_generated_university ILIKE '%stanford%' OR
                llm_generated_university ILIKE '%carnegie%'
              );
    """)
    results["phd_cs_accept_raw"] = cur.fetchone()[0]


    # --- ADD Q9 ---
    cur.execute("""
        SELECT COUNT(*)
        FROM applicants
        WHERE term ILIKE '%2026%'
          AND degree ILIKE '%phd%'
          AND llm_generated_program ILIKE '%computer science%'
          AND status ILIKE '%accept%'
          AND (
                llm_generated_university ILIKE '%georgetown%' OR
                llm_generated_university ILIKE '%mit%' OR
                llm_generated_university ILIKE '%stanford%' OR
                llm_generated_university ILIKE '%carnegie%'
              );
    """)
    results["phd_cs_accept_llm"] = cur.fetchone()[0]


    # --- ADD Q10A ---
    cur.execute("""
        SELECT degree,
               ROUND(
                    100.0 * SUM(CASE WHEN status ILIKE '%accept%' THEN 1 ELSE 0 END)
                    / NULLIF(COUNT(*), 0), 2)
        FROM applicants
        GROUP BY degree
        ORDER BY degree;
    """)
    results["acceptance_rate_by_degree"] = cur.fetchall()


    # --- ADD Q10B ---
    cur.execute("""
        SELECT degree,
               ROUND(AVG(gpa)::numeric, 2)
        FROM applicants
        GROUP BY degree
        ORDER BY degree;
    """)
    results["gpa_by_degree"] = cur.fetchall()


    conn.close()
    return results



# ---------------- FLASK ROUTES ----------------

@app.route("/")
def index():
    results = get_results()
    return render_template("index.html", results=results)


@app.route("/pull-data", methods=["POST"])
def pull_data():
    global scrape_running

    if scrape_running:
        return "A data pull is already running."

    scrape_running = True

    def run_pipeline():
        global scrape_running
        try:
            subprocess.run(["python", "../module_2/scrape.py"], check=True)
            subprocess.run(["python", "load-data.py"], check=True)
        finally:
            scrape_running = False

    threading.Thread(target=run_pipeline).start()
    return "Pull Data started. Click Update Analysis after it finishes."


@app.route("/update-analysis", methods=["POST"])
def update_analysis():
    if scrape_running:
        return "Cannot update while scraping is running."
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
