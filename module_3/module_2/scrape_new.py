"""
scrape_new.py - Working GradCafe scraper using correct URL + selectors.
"""

import urllib.request
import urllib.parse
import json
import time
import re
from bs4 import BeautifulSoup

BASE_URL = "https://www.thegradcafe.com"
SEARCH_URL = f"{BASE_URL}/survey/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15)"
}

DELAY = 2


def fetch(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req) as response:
            return response.read().decode("utf-8", errors="ignore")
    except:
        return None


def parse_detail(url):
    """Extract GPA/GRE/nationality/comments from detail page."""
    html = fetch(url)
    if not html:
        return {}

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    out = {
        "gpa": "",
        "gre_total": "",
        "gre_verbal": "",
        "gre_aw": "",
        "student_type": "",
        "comments": ""
    }

    gpa = re.search(r"GPA[:\s]*([0-3]?\.\d+|4\.0)", text)
    if gpa:
        out["gpa"] = gpa.group(1)

    gre_total = re.search(r"GRE[:\s]*(\d{3})", text)
    if gre_total:
        out["gre_total"] = gre_total.group(1)

    gre_v = re.search(r"Verbal[:\s]*(\d{2,3})", text)
    if gre_v:
        out["gre_verbal"] = gre_v.group(1)

    gre_aw = re.search(r"AW[:\s]*([0-6]\.?\d?)", text)
    if gre_aw:
        out["gre_aw"] = gre_aw.group(1)

    if "International" in text:
        out["student_type"] = "International"
    elif "American" in text:
        out["student_type"] = "American"

    comments = soup.find("div", class_="comment")
    if comments:
        out["comments"] = comments.get_text(" ", strip=True)

    return out



def parse_entry(div):
    """Parses one listing on the results page."""
    program_tag = div.find("div", class_="program")
    institution_tag = div.find("div", class_="institution")
    status_tag = div.find("span", class_="status")
    date_tag = div.find("span", class_="date")
    link = div.find("a", href=True)

    program = program_tag.get_text(strip=True) if program_tag else ""
    institution = institution_tag.get_text(strip=True) if institution_tag else ""
    status = status_tag.get_text(strip=True) if status_tag else ""
    date_added = date_tag.get_text(strip=True) if date_tag else ""

    url = BASE_URL + link["href"] if link else ""

    degree_type = ""
    if "PhD" in program:
        degree_type = "PhD"
    elif "Master" in program or "MS" in program:
        degree_type = "MS"

    term_match = re.search(r"(Fall|Spring|Summer|Winter)\s+(\d{4})", program)
    term = f"{term_match.group(1)} {term_match.group(2)}" if term_match else ""

    details = parse_detail(url)

    return {
        "program_name": program,
        "university": institution,
        "status": status,
        "date_added": date_added,
        "url": url,
        "degree_type": degree_type,
        "term_start": term,
        "gpa": details.get("gpa", ""),
        "gre_total": details.get("gre_total", ""),
        "gre_verbal": details.get("gre_verbal", ""),
        "gre_aw": details.get("gre_aw", ""),
        "student_type": details.get("student_type", ""),
        "comments": details.get("comments", "")
    }



def scrape(target=30000):
    print(f"Scraping {target} entries...")

    results = []
    page = 1

    while len(results) < target:
        url = f"{SEARCH_URL}?q=&t=a&p={page}"
        print(f"Scraping: {url}  ({len(results)} so far)")

        html = fetch(url)
        if not html:
            print("⚠ No HTML, stopping")
            break

        soup = BeautifulSoup(html, "html.parser")
        entries = soup.find_all("div", class_="result-entry")

        if not entries:
            print("⚠ No entries → stopping")
            break

        for e in entries:
            results.append(parse_entry(e))
            if len(results) >= target:
                break

        page += 1
        time.sleep(DELAY)

    print(f"Done. Total scraped: {len(results)}")
    return results



def main():
    data = scrape(30000)

    with open("applicant_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Saved → applicant_data.json")



if __name__ == "__main__":
    main()
