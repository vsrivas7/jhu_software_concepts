import requests
import time
import json

API_URL = "https://www.thegradcafe.com/api/survey/results?page={}&limit=250"

def scrape_gradcafe(target=30000):
    all_rows = []
    page = 1

    while len(all_rows) < target:
        url = API_URL.format(page)
        print(f"Fetching page {page}: {url}")

        try:
            r = requests.get(url, timeout=10)
            data = r.json()

            entries = data.get("results", [])
            if not entries:
                print("⚠ No more data received — stopping")
                break

            all_rows.extend(entries)
            print(f"Total collected: {len(all_rows)}")

            page += 1
            time.sleep(0.5)

        except Exception as e:
            print("Error:", e)
            break

    print(f"\nDone! Collected {len(all_rows)} rows.")
    with open("applicant_data.json", "w") as f:
        json.dump(all_rows, f, indent=2)

    print("Saved → applicant_data.json")


if __name__ == "__main__":
    scrape_gradcafe()
