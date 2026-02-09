"""
The Grad Cafe Scraper for Assignment
Scrapes data and exports to JSON format for LLM-based cleaning
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict, Optional
import re


class GradCafeScraper:
    """Scraper for The Grad Cafe admission results"""
    
    def __init__(self):
        self.base_url = "https://www.thegradcafe.com/survey/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def scrape_page(self, page_num: int = 1, params: Dict = None) -> List[Dict]:
        """Scrape a single page of results"""
        page_params = params.copy() if params else {}
        page_params['page'] = page_num
        
        try:
            response = requests.get(
                self.base_url, 
                headers=self.headers, 
                params=page_params, 
                timeout=15
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            table = soup.find('table')
            if not table:
                return results
            
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) < 4:
                        continue
                    
                    # Extract school/university name
                    school_raw = cells[0].get_text(strip=True).split('\n')[0] if cells[0] else ''
                    
                    # Extract program and degree
                    program_cell = cells[1].get_text(strip=True) if cells[1] else ''
                    program_parts = program_cell.split('\n')
                    program_raw = program_parts[0] if program_parts else ''
                    degree = program_parts[1].strip() if len(program_parts) > 1 else ''
                    
                    # Extract added date
                    added_on = cells[2].get_text(strip=True) if cells[2] else ''
                    
                    # Extract decision and details
                    decision_cell = cells[3].get_text(separator='|', strip=True) if cells[3] else ''
                    decision_parts = decision_cell.split('|')
                    
                    decision = decision_parts[0].strip() if decision_parts else ''
                    
                    # Extract additional details
                    season = ''
                    applicant_status = ''
                    gpa = ''
                    
                    for part in decision_parts[1:]:
                        part = part.strip()
                        if 'Fall' in part or 'Spring' in part:
                            season = part
                        elif 'International' in part or 'American' in part:
                            applicant_status = part
                        elif 'GPA' in part:
                            gpa_match = re.search(r'GPA\s*([\d.]+)', part)
                            if gpa_match:
                                gpa = gpa_match.group(1)
                    
                    # Get result ID
                    see_more_link = row.find('a', href=re.compile(r'/result/\d+'))
                    result_id = ''
                    if see_more_link:
                        result_id = see_more_link['href'].split('/')[-1]
                    
                    result = {
                        'university': school_raw,      # Raw university name (needs cleaning)
                        'program': program_raw,         # Raw program name (needs cleaning)
                        'degree': degree,
                        'decision': decision,
                        'season': season,
                        'applicant_status': applicant_status,
                        'gpa': gpa,
                        'added_on': added_on,
                        'result_id': result_id,
                        'page_scraped': page_num
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    print(f"Error parsing row: {e}")
                    continue
            
            return results
            
        except requests.RequestException as e:
            print(f"Error fetching page {page_num}: {e}")
            return []
    
    def scrape_dataset(self, 
                      num_pages: int = 100,
                      output_file: str = 'gradcafe_data.json',
                      delay: float = 1.5,
                      params: Dict = None) -> List[Dict]:
        """
        Scrape multiple pages and save to JSON
        
        Args:
            num_pages: Number of pages to scrape
            output_file: Output JSON file path
            delay: Delay between requests in seconds
            params: Query parameters for filtering
        """
        all_results = []
        
        print(f"Scraping {num_pages} pages from The Grad Cafe...")
        print(f"Output file: {output_file}")
        print(f"Delay: {delay}s between requests\n")
        
        for page in range(1, num_pages + 1):
            print(f"Scraping page {page}/{num_pages} | " +
                  f"Total records: {len(all_results)}", end='\r')
            
            results = self.scrape_page(page_num=page, params=params)
            
            if not results:
                print(f"\nWarning: Page {page} returned no results")
                # Continue anyway in case it's a temporary issue
            else:
                all_results.extend(results)
            
            # Save progress periodically
            if page % 10 == 0:
                with open(output_file, 'w') as f:
                    json.dump(all_results, f, indent=2)
                print(f"\nProgress saved: {len(all_results)} records")
            
            if page < num_pages:
                time.sleep(delay)
        
        # Final save
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n\nScraping completed!")
        print(f"Total records: {len(all_results)}")
        print(f"Saved to: {output_file}")
        
        # Show statistics
        if all_results:
            universities = set(r['university'] for r in all_results if r['university'])
            programs = set(r['program'] for r in all_results if r['program'])
            
            print(f"\nDataset Statistics:")
            print(f"  Unique universities (raw): {len(universities)}")
            print(f"  Unique programs (raw): {len(programs)}")
            print(f"  Example universities: {list(universities)[:5]}")
            print(f"  Example programs: {list(programs)[:5]}")
            print(f"\nNote: These are RAW values that need cleaning with the LLM tool")
        
        return all_results


def main():
    """Main function to run the scraper"""
    scraper = GradCafeScraper()
    
    print("="*60)
    print("Grad Cafe Scraper for Assignment")
    print("="*60)
    print("\nThis scraper will collect data for the LLM cleaning assignment.")
    print("The data will be exported in JSON format.\n")
    
    # Get user input
    try:
        num_pages = int(input("How many pages to scrape? (e.g., 100 for ~2000 records): ").strip())
    except ValueError:
        print("Invalid input. Using default: 100 pages")
        num_pages = 100
    
    output_file = input("Output filename (default: gradcafe_data.json): ").strip()
    if not output_file:
        output_file = 'gradcafe_data.json'
    
    # Ensure .json extension
    if not output_file.endswith('.json'):
        output_file += '.json'
    
    print(f"\nConfiguration:")
    print(f"  Pages: {num_pages}")
    print(f"  Output: {output_file}")
    print(f"  Estimated records: ~{num_pages * 20}")
    print(f"  Estimated time: ~{num_pages * 1.5 / 60:.1f} minutes\n")
    
    confirm = input("Start scraping? (y/n): ").lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Run the scraper
    results = scraper.scrape_dataset(
        num_pages=num_pages,
        output_file=output_file,
        delay=1.5
    )
    
    print(f"\n{'='*60}")
    print("Next Steps:")
    print("="*60)
    print(f"1. Your scraped data is in: {output_file}")
    print(f"2. Add the llm_hosting module to your repository")
    print(f"3. Run: python app.py --file \"{output_file}\" > out.json")
    print(f"4. The LLM will clean the 'university' and 'program' fields")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()