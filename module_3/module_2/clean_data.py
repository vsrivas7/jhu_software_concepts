import json

INPUT_FILE = "llm_extended_applicant_data.json"   # <-- FIXED
OUTPUT_FILE = "llm_cleaned.json"

def clean_record(rec):
    """Return a cleaned applicant record."""
    return {
        "program": rec.get("program_name", ""),
        "comments": rec.get("comments", ""),
        "date_added": rec.get("date_added", ""),
        "url": rec.get("entry_url", rec.get("url", "")),
        "status": rec.get("status", ""),
        "term": rec.get("term_start", ""),
        "us_or_international": rec.get("student_type", ""),
        "gpa": try_float(rec.get("gpa")),
        "gre": try_float(rec.get("gre_total")),
        "gre_v": try_float(rec.get("gre_verbal")),
        "gre_aw": try_float(rec.get("gre_aw", rec.get("gre_writing"))),
        "degree": rec.get("degree_type", ""),
        "llm_generated_program": rec.get("cleaned_program", ""),
        "llm_generated_university": rec.get("cleaned_university", "")
    }

def try_float(x):
    """Convert to float or return None."""
    try:
        return float(x)
    except:
        return None

def main():
    print(f"Loading: {INPUT_FILE}")
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    # If file contains {"applicants": [...]}, extract list
    if isinstance(data, dict) and "applicants" in data:
        data = data["applicants"]

    print(f"Cleaning {len(data)} records...")

    cleaned = [clean_record(rec) for rec in data]

    with open(OUTPUT_FILE, "w") as f:
        json.dump(cleaned, f, indent=2)

    print(f"Saved cleaned file → {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
