CREATE TABLE IF NOT EXISTS applicants (
    id              SERIAL PRIMARY KEY,
    university      TEXT,
    program         TEXT,
    degree          TEXT,
    decision        TEXT,
    season          TEXT,
    applicant_status TEXT,
    gpa             TEXT,
    added_on        TEXT,
    result_id       TEXT UNIQUE,
    page_scraped    INTEGER,
    us_or_international TEXT,
    term            TEXT
);

CREATE TABLE IF NOT EXISTS ingestion_watermarks (
    source      TEXT PRIMARY KEY,
    last_seen   TEXT,
    updated_at  TIMESTAMPTZ DEFAULT now()
);
