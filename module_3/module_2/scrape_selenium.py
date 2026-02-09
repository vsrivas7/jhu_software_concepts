"""
scrape_selenium.py – Selenium GradCafe Scraper
Works with new GradCafe UI (2026)
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

TARGET_COUNT = 30000

def start_browser():
    """Start Chrome with options that bypass anti-bot filters."""
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36")

    # OPTIONAL: make it headless
    # options.add_argument("--headless=new")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


def parse_entry(div):
    """Extract key fields from a single GradCafe entry <div>."""
    try:
        text = div.get_text(" ", strip=True)

        program_elem = div.find("h3", class_="program")
        uni_elem = div.find("span", class_="institution")
        status_elem = div.find("span", class_="status")
        date_elem = div.find("span", class_="date")
        profile_elem = div.find("div", class_="details")
        comments_elem = div.find("div", class_="notes")

        return {
            "program_name": program_elem.get_text(strip=True) if program_elem else "",
            "university": uni_elem.get_text(strip=True) if uni_elem else "",
            "status": status_elem.get_text(strip=True) if status_elem else "",
            "date_added": date_elem.get_text(strip=True) if date_elem else "",
            "comments": comments_elem.get_text(strip=True) if comments_elem else "",
            "raw_details": profile_elem.get_text(strip=True) if profile_elem else "",
        }
    except Exception:
        return None


def scrape_gradcafe():
    driver = start_browser()

    print(f"Scraping {TARGET_COUNT} entries…")
    url = "https://www.thegradcafe.com/survey/"
    driver.get(url)
    time.sleep(3)

    data = []
    last_height = 0

    while len(data) < TARGET_COUNT:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        entries = soup.find_all("div", class_="result-entry")

        for e in entries:
            parsed = parse_entry(e)
            if parsed:
                data.append(parsed)

        print(f"[+] Collected: {len(data)} entries")

        # Scroll to load more results
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("No new entries loading — stopping.")
            break
        last_height = new_height

    driver.quit()
    print(f"Done. Total scraped: {len(data)}")

    with open("applicant_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Saved → applicant_data.json")


if __name__ == "__main__":
    scrape_gradcafe()
