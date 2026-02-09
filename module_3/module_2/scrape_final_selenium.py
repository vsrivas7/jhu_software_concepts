"""
The Grad Cafe Web Scraper
Scrapes graduate school admission results from thegradcafe.com
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from typing import List, Dict, Optional
import re


class GradCafeScraper:
    """Scraper for The Grad Cafe admission results"""
    
    def __init__(self):
        self.base_url = "https://www.thegradcafe.com/survey/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def scrape_page(self, url: str = None, params: Dict = None) -> List[Dict]:
        """
        Scrape a single page of results
        
        Args:
            url: URL to scrape (defaults to base_url)
            params: Query parameters for filtering
            
        Returns:
            List of dictionaries containing admission results
        """
        if url is None:
            url = self.base_url
            
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Find the results table
            table = soup.find('table')
            if not table:
                print("No table found on page")
                return results
            
            # Find all rows (skip header row)
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) < 4:
                        continue
                    
                    # Extract school name
                    school = cells[0].get_text(strip=True).split('\n')[0] if cells[0] else ''
                    
                    # Extract program and degree
                    program_cell = cells[1].get_text(strip=True) if cells[1] else ''
                    program_parts = program_cell.split('\n')
                    program = program_parts[0] if program_parts else ''
                    degree = program_parts[1] if len(program_parts) > 1 else ''
                    
                    # Extract added date
                    added_on = cells[2].get_text(strip=True) if cells[2] else ''
                    
                    # Extract decision and details
                    decision_cell = cells[3].get_text(separator='|', strip=True) if cells[3] else ''
                    decision_parts = decision_cell.split('|')
                    
                    decision = decision_parts[0] if decision_parts else ''
                    
                    # Extract additional details (season, status, GPA, etc.)
                    details = {}
                    for part in decision_parts[1:]:
                        part = part.strip()
                        if 'Fall' in part or 'Spring' in part:
                            details['season'] = part
                        elif 'International' in part or 'American' in part:
                            details['status'] = part
                        elif 'GPA' in part:
                            gpa_match = re.search(r'GPA\s*([\d.]+)', part)
                            if gpa_match:
                                details['gpa'] = gpa_match.group(1)
                    
                    # Get the "See More" link for additional details
                    see_more_link = row.find('a', href=re.compile(r'/result/\d+'))
                    result_id = ''
                    if see_more_link:
                        result_id = see_more_link['href'].split('/')[-1]
                    
                    result = {
                        'school': school,
                        'program': program,
                        'degree': degree,
                        'added_on': added_on,
                        'decision': decision,
                        'season': details.get('season', ''),
                        'applicant_status': details.get('status', ''),
                        'gpa': details.get('gpa', ''),
                        'result_id': result_id,
                        'url': f"https://www.thegradcafe.com/result/{result_id}" if result_id else ''
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    print(f"Error parsing row: {e}")
                    continue
            
            return results
            
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return []
    
    def scrape_multiple_pages(self, num_pages: int = 5, params: Dict = None, delay: float = 1.0) -> pd.DataFrame:
        """
        Scrape multiple pages of results
        
        Args:
            num_pages: Number of pages to scrape
            params: Query parameters for filtering
            delay: Delay between requests in seconds
            
        Returns:
            DataFrame containing all scraped results
        """
        all_results = []
        
        for page in range(1, num_pages + 1):
            print(f"Scraping page {page}/{num_pages}...")
            
            page_params = params.copy() if params else {}
            page_params['page'] = page
            
            results = self.scrape_page(params=page_params)
            all_results.extend(results)
            
            # Be respectful to the server
            if page < num_pages:
                time.sleep(delay)
        
        df = pd.DataFrame(all_results)
        print(f"\nTotal results scraped: {len(df)}")
        return df
    
    def scrape_with_filters(self, 
                           degree: Optional[str] = None,
                           season: Optional[str] = None,
                           decision: Optional[str] = None,
                           program: Optional[str] = None,
                           school: Optional[str] = None,
                           num_pages: int = 5) -> pd.DataFrame:
        """
        Scrape results with specific filters
        
        Args:
            degree: Degree type (e.g., 'PhD', 'Masters')
            season: Season (e.g., 'Fall 2026', 'Spring 2025')
            decision: Decision type (e.g., 'Accepted', 'Rejected')
            program: Program name
            school: School name
            num_pages: Number of pages to scrape
            
        Returns:
            DataFrame containing filtered results
        """
        params = {}
        
        # Build query string
        q_parts = []
        if degree:
            q_parts.append(degree)
        if program:
            q_parts.append(program)
        if school:
            q_parts.append(school)
            
        if q_parts:
            params['q'] = ' '.join(q_parts)
        
        # Note: The website uses query parameters differently
        # You may need to adjust these based on the actual API
        
        return self.scrape_multiple_pages(num_pages=num_pages, params=params)


def main():
    """Example usage of the scraper"""
    scraper = GradCafeScraper()
    
    # Example 1: Scrape first 3 pages of general results
    print("Example 1: Scraping general results...")
    df = scraper.scrape_multiple_pages(num_pages=3)
    
    if not df.empty:
        # Display first few results
        print("\nFirst 5 results:")
        print(df.head())
        
        # Save to CSV
        output_file = 'gradcafe_results.csv'
        df.to_csv(output_file, index=False)
        print(f"\nResults saved to {output_file}")
        
        # Display some statistics
        print("\n=== Statistics ===")
        print(f"Total results: {len(df)}")
        print(f"\nDecision breakdown:")
        print(df['decision'].value_counts())
        print(f"\nTop 5 schools:")
        print(df['school'].value_counts().head())
        print(f"\nTop 5 programs:")
        print(df['program'].value_counts().head())
    
    # Example 2: Scrape with search query
    print("\n\nExample 2: Scraping Computer Science PhD results...")
    df_cs = scraper.scrape_multiple_pages(num_pages=2, params={'q': 'Computer Science PhD'})
    
    if not df_cs.empty:
        print(f"Found {len(df_cs)} Computer Science PhD results")
        df_cs.to_csv('gradcafe_cs_phd.csv', index=False)
        print("Saved to gradcafe_cs_phd.csv")


if __name__ == "__main__":
    main()