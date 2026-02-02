"""
scrape.py - Grad Café Web Scraper

This module scrapes graduate school admissions data from Grad Café.
It collects applicant information including program details, admission status,
test scores, and other relevant metrics.

Author: [Your Name] - [Your JHED ID]
Module: Module 2 - Web Scraping
"""

import urllib.request
import urllib.parse
import urllib.robotparser
import json
import time
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional


class GradCafeScraper:
    """
    A web scraper for collecting graduate school admissions data from Grad Café.
    
    This scraper respects robots.txt and implements rate limiting to avoid
    overwhelming the server.
    """
    
    def __init__(self, base_url: str = "https://www.thegradcafe.com"):
        """
        Initialize the GradCafeScraper.
        
        Args:
            base_url: The base URL for Grad Café
        """
        self.base_url = base_url
        self.search_url = f"{base_url}/search/index.php"
        self.user_agent = "Mozilla/5.0 (compatible; GradCafeResearchBot/1.0)"
        self.headers = {'User-Agent': self.user_agent}
        self.delay = 2  # Delay between requests in seconds
        
    def check_robots_txt(self) -> bool:
        """
        Check if scraping is allowed according to robots.txt.
        
        Returns:
            True if scraping is allowed, False otherwise
        """
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"{self.base_url}/robots.txt")
        try:
            rp.read()
            can_fetch = rp.can_fetch(self.user_agent, self.search_url)
            print(f"robots.txt check: {'Allowed' if can_fetch else 'Disallowed'}")
            return can_fetch
        except Exception as e:
            print(f"Error reading robots.txt: {e}")
            return False
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[str]:
        """
        Make an HTTP request with error handling.
        
        Args:
            url: The URL to request
            params: Optional query parameters
            
        Returns:
            The response HTML as a string, or None if request failed
        """
        try:
            if params:
                url = f"{url}?{urllib.parse.urlencode(params)}"
            
            req = urllib.request.Request(url, headers=self.headers)
            
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    html = response.read().decode('utf-8')
                    return html
                else:
                    print(f"Request failed with status: {response.status}")
                    return None
                    
        except urllib.error.HTTPError as e:
            print(f"HTTP Error {e.code}: {e.reason}")
            return None
        except urllib.error.URLError as e:
            print(f"URL Error: {e.reason}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    
    def _parse_entry(self, row) -> Optional[Dict]:
        """
        Parse a single table row containing applicant data.
        
        Args:
            row: BeautifulSoup table row element
            
        Returns:
            Dictionary containing parsed applicant data, or None if parsing failed
        """
        try:
            cells = row.find_all('td')
            
            # The structure varies, so we need to be flexible
            if len(cells) < 4:
                return None
            
            # Extract the unique URL/ID for this entry
            # Typically found in a link within the row
            entry_link = row.find('a', href=re.compile(r'survey'))
            entry_url = ""
            if entry_link:
                entry_url = self.base_url + entry_link.get('href', '')
            
            # Initialize data dictionary with all required fields
            data = {
                'program_name': '',
                'university': '',
                'comments': '',
                'date_added': '',
                'url': entry_url,
                'status': '',
                'decision_date': '',
                'semester': '',
                'year': '',
                'student_type': '',  # International/American
                'degree_type': '',   # Masters/PhD
                'gpa': '',
                'gre_total': '',
                'gre_verbal': '',
                'gre_writing': ''
            }
            
            # Parse institution and program (usually in first cell)
            if len(cells) > 0:
                # Extract university and program
                institution_cell = cells[0]
                institution_text = institution_cell.get_text(strip=True)
                
                # Try to split university from program
                # Common patterns: "University Name, Program Name" or "Program Name at University"
                if ',' in institution_text:
                    parts = institution_text.split(',', 1)
                    data['university'] = parts[0].strip()
                    data['program_name'] = parts[1].strip() if len(parts) > 1 else ''
                else:
                    # If no clear delimiter, put everything in program_name
                    data['program_name'] = institution_text
            
            # Parse decision information (Accepted/Rejected/Waitlisted)
            if len(cells) > 1:
                decision_cell = cells[1]
                decision_text = decision_cell.get_text(strip=True)
                
                # Extract status
                if 'Accepted' in decision_text:
                    data['status'] = 'Accepted'
                elif 'Rejected' in decision_text:
                    data['status'] = 'Rejected'
                elif 'Wait' in decision_text:
                    data['status'] = 'Waitlisted'
                elif 'Interview' in decision_text:
                    data['status'] = 'Interview'
                else:
                    data['status'] = decision_text
            
            # Parse date added
            if len(cells) > 2:
                date_cell = cells[2]
                data['date_added'] = date_cell.get_text(strip=True)
            
            # Parse program details (degree, season, etc.)
            if len(cells) > 3:
                details_cell = cells[3]
                details_text = details_cell.get_text(strip=True)
                
                # Extract degree type
                if 'PhD' in details_text or 'Ph.D' in details_text:
                    data['degree_type'] = 'PhD'
                elif 'Masters' in details_text or 'MS' in details_text or 'MA' in details_text or "Master's" in details_text:
                    data['degree_type'] = 'Masters'
                
                # Extract semester and year
                # Common patterns: "F20", "S21", "Fall 2020", "Spring 2021"
                season_pattern = re.search(r'(Fall|Spring|Summer|Winter|F|S|W|Su)\s*[\'"]?(\d{2,4})', details_text)
                if season_pattern:
                    season = season_pattern.group(1)
                    year = season_pattern.group(2)
                    
                    # Standardize season
                    season_map = {'F': 'Fall', 'S': 'Spring', 'W': 'Winter', 'Su': 'Summer'}
                    if season in season_map:
                        season = season_map[season]
                    
                    data['semester'] = season
                    
                    # Handle 2-digit vs 4-digit year
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year
                    data['year'] = year
            
            # Parse student profile (GRE, GPA, etc.)
            # This is often in a later cell or needs special handling
            if len(cells) > 4:
                profile_cell = cells[4]
                profile_text = profile_cell.get_text(strip=True)
                
                # Extract GPA
                gpa_pattern = re.search(r'GPA[:\s]*([0-3]?\.\d+|[0-4]\.\d+)', profile_text, re.IGNORECASE)
                if gpa_pattern:
                    data['gpa'] = gpa_pattern.group(1)
                
                # Extract GRE scores
                gre_pattern = re.search(r'GRE[:\s]*(\d{3})', profile_text, re.IGNORECASE)
                if gre_pattern:
                    data['gre_total'] = gre_pattern.group(1)
                
                gre_v_pattern = re.search(r'V[:\s]*(\d{2,3})', profile_text, re.IGNORECASE)
                if gre_v_pattern:
                    data['gre_verbal'] = gre_v_pattern.group(1)
                
                gre_aw_pattern = re.search(r'(?:AW|A|W)[:\s]*([0-6]\.?\d?)', profile_text, re.IGNORECASE)
                if gre_aw_pattern:
                    data['gre_writing'] = gre_aw_pattern.group(1)
                
                # Extract student type
                if 'International' in profile_text or 'I' in profile_text:
                    data['student_type'] = 'International'
                elif 'American' in profile_text or 'U' in profile_text or 'Domestic' in profile_text:
                    data['student_type'] = 'American'
            
            # Extract comments if available (may be in a separate section)
            comment_elem = row.find('div', class_=re.compile('comment', re.IGNORECASE))
            if comment_elem:
                data['comments'] = comment_elem.get_text(strip=True)
            
            return data
            
        except Exception as e:
            print(f"Error parsing entry: {e}")
            return None
    
    def scrape_data(self, target_count: int = 30000) -> List[Dict]:
        """
        Scrape graduate admissions data from Grad Café.
        
        Args:
            target_count: Minimum number of entries to collect
            
        Returns:
            List of dictionaries containing applicant data
        """
        print(f"Starting scrape with target of {target_count} entries...")
        
        all_data = []
        page = 1
        consecutive_empty = 0
        max_consecutive_empty = 5
        
        while len(all_data) < target_count:
            print(f"Scraping page {page} (collected {len(all_data)} entries so far)...")
            
            # Build search parameters
            # Grad Café uses pagination - adjust based on actual site structure
            params = {
                'q': '',  # Empty query to get all results
                'page': page,
                'pp': 250  # Results per page (adjust based on site limits)
            }
            
            html = self._make_request(self.search_url, params)
            
            if not html:
                print("Failed to retrieve page, stopping...")
                break
            
            # Parse the HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find the results table
            # The actual class/id may vary - inspect the website to find correct selector
            results_table = soup.find('table', class_=re.compile('submission-table|results', re.IGNORECASE))
            
            if not results_table:
                # Try alternative selectors
                results_table = soup.find('table', id=re.compile('results'))
            
            if not results_table:
                print("Could not find results table on page")
                consecutive_empty += 1
                if consecutive_empty >= max_consecutive_empty:
                    print("Too many empty pages, stopping...")
                    break
                page += 1
                time.sleep(self.delay)
                continue
            
            # Find all result rows
            rows = results_table.find_all('tr')[1:]  # Skip header row
            
            if not rows:
                print("No results found on this page")
                consecutive_empty += 1
                if consecutive_empty >= max_consecutive_empty:
                    print("Too many empty pages, stopping...")
                    break
                page += 1
                time.sleep(self.delay)
                continue
            
            consecutive_empty = 0
            
            # Parse each row
            for row in rows:
                entry_data = self._parse_entry(row)
                if entry_data:
                    all_data.append(entry_data)
            
            print(f"Extracted {len(rows)} entries from page {page}")
            
            page += 1
            
            # Respect rate limiting
            time.sleep(self.delay)
        
        print(f"Scraping complete. Collected {len(all_data)} entries.")
        return all_data
    
    def save_data(self, data: List[Dict], filename: str = "applicant_data.json"):
        """
        Save scraped data to a JSON file.
        
        Args:
            data: List of applicant data dictionaries
            filename: Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def load_data(self, filename: str = "applicant_data.json") -> List[Dict]:
        """
        Load scraped data from a JSON file.
        
        Args:
            filename: Input filename
            
        Returns:
            List of applicant data dictionaries
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Loaded {len(data)} entries from {filename}")
            return data
        except Exception as e:
            print(f"Error loading data: {e}")
            return []


def main():
    """Main execution function."""
    # Initialize scraper
    scraper = GradCafeScraper()
    
    # Check robots.txt
    if not scraper.check_robots_txt():
        print("Warning: Scraping may not be allowed according to robots.txt")
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            print("Exiting...")
            return
    
    # Scrape data
    data = scraper.scrape_data(target_count=30000)
    
    # Save data
    scraper.save_data(data, "applicant_data.json")
    
    print(f"\nScraping complete!")
    print(f"Total entries collected: {len(data)}")


if __name__ == "__main__":
    main()