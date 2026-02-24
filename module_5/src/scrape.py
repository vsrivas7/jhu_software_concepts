"""Grad Cafe Scraper."""

# pylint: disable=too-many-locals, too-many-nested-blocks

import json
import re
import time
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup


class GradCafeScraper:
    """Scraper for The Grad Cafe admission results."""

    def __init__(self) -> None:
        self.base_url = "https://www.thegradcafe.com/survey/"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            )
        }

    def scrape_page(
        self,
        page_num: int = 1,
        params: Optional[Dict] = None,
    ) -> List[Dict]:
        """Scrape a single page of results."""
        page_params = params.copy() if params else {}
        page_params["page"] = page_num

        try:
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=page_params,
                timeout=15,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            results: List[Dict] = []

            table = soup.find("table")
            if not table:
                return results

            rows = table.find_all("tr")[1:]  # Skip header

            for row in rows:
                try:
                    cells = row.find_all("td")
                    if len(cells) < 4:
                        continue

                    school_raw = (
                        cells[0].get_text(strip=True).split("\n")[0]
                        if cells[0] else ""
                    )

                    program_cell = (
                        cells[1].get_text(strip=True)
                        if cells[1] else ""
                    )

                    program_parts = program_cell.split("\n")
                    program_raw = program_parts[0] if program_parts else ""
                    degree = (
                        program_parts[1].strip()
                        if len(program_parts) > 1 else ""
                    )

                    added_on = (
                        cells[2].get_text(strip=True)
                        if cells[2] else ""
                    )

                    decision_cell = (
                        cells[3].get_text(separator="|", strip=True)
                        if cells[3] else ""
                    )

                    decision_parts = decision_cell.split("|")
                    decision = (
                        decision_parts[0].strip()
                        if decision_parts else ""
                    )

                    season = ""
                    applicant_status = ""
                    gpa = ""

                    for part in decision_parts[1:]:
                        part = part.strip()
                        if "Fall" in part or "Spring" in part:
                            season = part
                        elif "International" in part or "American" in part:
                            applicant_status = part
                        elif "GPA" in part:
                            gpa_match = re.search(r"GPA\s*([\d.]+)", part)
                            if gpa_match:
                                gpa = gpa_match.group(1)

                    see_more_link = row.find(
                        "a",
                        href=re.compile(r"/result/\d+"),
                    )

                    result_id = ""
                    if see_more_link:
                        result_id = see_more_link["href"].split("/")[-1]

                    result = {
                        "university": school_raw,
                        "program": program_raw,
                        "degree": degree,
                        "decision": decision,
                        "season": season,
                        "applicant_status": applicant_status,
                        "gpa": gpa,
                        "added_on": added_on,
                        "result_id": result_id,
                        "page_scraped": page_num,
                    }

                    results.append(result)

                except (AttributeError, ValueError):
                    # Skip malformed rows safely
                    continue

            return results

        except requests.RequestException:
            return []

    def scrape_dataset(
        self,
        num_pages: int = 1,
        output_file: str = "gradcafe_data.json",
        delay: float = 0.0,
        params: Optional[Dict] = None,
    ) -> List[Dict]:
        """Scrape multiple pages and save to JSON."""
        all_results: List[Dict] = []

        for page in range(1, num_pages + 1):
            results = self.scrape_page(page_num=page, params=params)
            if results:
                all_results.extend(results)

            if delay > 0 and page < num_pages:
                time.sleep(delay)

        with open(output_file, "w", encoding="utf-8") as file_obj:
            json.dump(all_results, file_obj, indent=2)

        return all_results


def scrape_data() -> List[Dict]:
    """Wrapper used by Flask app."""
    local_scraper = GradCafeScraper()
    return local_scraper.scrape_dataset(num_pages=1)


if __name__ == "__main__":
    standalone_scraper = GradCafeScraper()
    standalone_scraper.scrape_dataset(num_pages=1)
