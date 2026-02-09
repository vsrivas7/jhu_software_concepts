import psycopg

DB_NAME = "gradcafe"
DB_USER = None
DB_HOST = "localhost"
DB_PORT = 5432


def run_query(cursor, label, sql):
    print("\n" + "="*80)
    print(label)
    print("-"*80)
    cursor.execute(sql)
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    return rows


def main():
    conn = psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()

    # 1. How many entries are for Fall 2026?
    run_query(cur, "1. Fall 2026 Applicants", """
        SELECT COUNT(*)
        FROM applicants
        WHERE term ILIKE '%fall%' AND term ILIKE '%2026%';
    """)

    # 2. Percentage of international students
    run_query(cur, "2. International Students (%)", """
        SELECT ROUND(
            100.0 * SUM(
                CASE WHEN us_or_international NOT IN ('American','Other')
                     AND us_or_international IS NOT NULL
                THEN 1 ELSE 0 END
            ) / NULLIF(COUNT(*), 0),
        2)
        FROM applicants;
    """)

    # 3. Average GPA, GRE, GRE-V, GRE-AW
    run_query(cur, "3. Average GPA, GRE(Q), GRE(V), GRE(AW)", """
        SELECT
            ROUND(AVG(gpa)::numeric, 2),
            ROUND(AVG(gre)::numeric, 2),
            ROUND(AVG(gre_v)::numeric, 2),
            ROUND(AVG(gre_aw)::numeric, 2)
        FROM applicants;
    """)

    # 4. Average GPA of American students in Fall 2026
    run_query(cur, "4. Avg GPA (American, Fall 2026)", """
        SELECT ROUND(AVG(gpa)::numeric, 2)
        FROM applicants
        WHERE us_or_international = 'American'
          AND term ILIKE '%fall%' AND term ILIKE '%2026%';
    """)

    # 5. Percent of Fall 2025 entries that are Acceptances
    run_query(cur, "5. Fall 2025 Acceptance %", """
        SELECT ROUND(
            100.0 * SUM(CASE WHEN status ILIKE '%accept%' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0),
        2)
        FROM applicants
        WHERE term ILIKE '%fall%' AND term ILIKE '%2025%';
    """)

    # 6. Avg GPA of accepted Fall 2026 applicants
    run_query(cur, "6. Avg GPA of Accepted Applicants (Fall 2026)", """
        SELECT ROUND(AVG(gpa)::numeric, 2)
        FROM applicants
        WHERE term ILIKE '%fall%'
          AND term ILIKE '%2026%'
          AND status ILIKE '%accept%';
    """)

    # 7. JHU MS CS applicants
    run_query(cur, "7. JHU MS CS Applicants", """
        SELECT COUNT(*)
        FROM applicants
        WHERE llm_generated_university ILIKE '%johns hopkins%'
          AND degree ILIKE '%ms%'
          AND llm_generated_program ILIKE '%computer science%';
    """)

    # 8. 2026 PhD CS acceptances using raw fields
    run_query(cur, "8. 2026 PhD CS Acceptances (Raw Fields)", """
        SELECT COUNT(*)
        FROM applicants
        WHERE term ILIKE '%2026%'
          AND degree ILIKE '%phd%'
          AND program ILIKE '%computer%'
          AND status ILIKE '%accept%'
          AND (
                university ILIKE '%georgetown%' OR
                university ILIKE '%mit%' OR
                university ILIKE '%stanford%' OR
                university ILIKE '%carnegie%'
              );
    """)

    # 9. 2026 PhD CS acceptances using LLM-generated fields
    run_query(cur, "9. 2026 PhD CS Acceptances (LLM Fields)", """
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

    # ----------------------------
    # ADDITIONAL QUESTIONS (Required)
    # ----------------------------

    # 10A. Acceptance rate by degree type
    run_query(cur, "10A. Acceptance Rate by Degree Type", """
        SELECT degree,
               ROUND(
                    100.0 * SUM(CASE WHEN status ILIKE '%accept%' THEN 1 ELSE 0 END)
                    / NULLIF(COUNT(*), 0),
               2) AS acceptance_rate
        FROM applicants
        GROUP BY degree
        ORDER BY acceptance_rate DESC NULLS LAST;
    """)

    # 10B. Average GPA by degree type
    run_query(cur, "10B. Average GPA by Degree Type", """
        SELECT degree,
               ROUND(AVG(gpa)::numeric, 2) AS avg_gpa
        FROM applicants
        GROUP BY degree
        ORDER BY avg_gpa DESC NULLS LAST;
    """)

    conn.close()


if __name__ == "__main__":
    main()
