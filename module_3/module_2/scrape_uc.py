import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time
import json

BASE = "https://www.thegradcafe.com/survey/?p={}"

def scrape_page(driver, page):
    url = BASE.format(page)
    print(f"Scraping page {page} → {url}")
    driver.get(url)
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    rows = soup.select("table.submission-table tbody tr")

    if not rows:
        print("⚠ No rows found on page")
        return []

    results = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 3:
            continue

        entry = {
            "program_name": cols[0].get_text(strip=True),
            "decision": cols[1].get_text(strip=True),
            "date": cols[2].get_text(strip=True),
            "details": cols[3].get_text(strip=True) if len(cols) > 3 else "",
        }

        results.append(entry)

    return results


def main():
    print("Launching undetected Chrome…")

    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(version_main=144, options=options)

    all_entries = []

    for page in range(1, 300):
        page_data = scrape_page(driver, page)
        if not page_data:
            print("Stopping — empty page encountered.")
            break
        all_entries.extend(page_data)

        print(f"Total so far: {len(all_entries)}")

        time.sleep(1)

    driver.quit()

    print(f"Scraped {len(all_entries)} entries.")
    with open("applicant_data.json", "w") as f:
        json.dump(all_entries, f, indent=2)

    print("Saved → applicant_data.json")


if __name__ == "__main__":
    main()
