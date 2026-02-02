# Module 2: Web Scraping Assignment

## Project Overview
Web scraper for GradCafe graduate admissions data.

## Files Generated
| File | Description |
|------|-------------|
| `scrape_gradcafe_final.py` | Main scraping script |
| `applicant_data.json` | Complete dataset with metadata |
| `sample_data.json` | First 10 entries for verification |
| `robots.txt` | Evidence of robots.txt compliance |
| `requirements.txt` | Python requirements |
| `README.md` | This documentation file |
| `progress_page_*.json` | Incremental progress files |

## Data Statistics
- **Total Applicants**: 29999
- **Unique Universities**: 1711
- **Unique Programs**: 3109
- **Status Breakdown**:
  - Unknown: 29999 (100.0%)

## Implementation Details
### Libraries Used
- `urllib`: HTTP requests and URL handling
- `re`: Regular expressions for HTML parsing
- `json`: Data serialization
- `html`: HTML entity decoding
- `datetime`: Timestamp generation

### Key Functions
1. `fetch_page()`: HTTP client with headers
2. `parse_gradcafe_html()`: HTML table parser
3. `parse_applicant_row()`: Data extraction from table cells
4. `extract_status()`, `extract_date()`, etc.: Field-specific parsers

### Data Fields Collected
All fields as per assignment requirements:
- `program_name`: Graduate program name
- `university`: University name
- `status`: Admission decision
- `date_added`: When added to GradCafe
- `entry_url`: Source URL
- `gpa`: Undergraduate GPA
- `gre_total`: Total GRE score
- `gre_verbal`: GRE Verbal score
- `gre_aw`: GRE Analytical Writing
- `degree_type`: Degree type (PhD, Masters, etc.)
- `student_type`: International/American
- `term_start`: Program start term
- `comments`: Additional comments

## Sample Entry
```json
{
  "program_name": "Statistics PhD",
  "university": "University of South Carolina",
  "comments": "Total comments Open options See More Report",
  "date_added": "February 01, 2026",
  "entry_url": "https://www.thegradcafe.com/survey/index.php?page=1",
  "status": "Unknown",
  "term_start": "",
  "student_type": "",
  "gre_total": "",
  "gre_verbal": "",
  "gre_aw": "",
  "degree_type": "PhD",
  "gpa": ""
}
```

## Running the Scraper
```bash
# For testing (100 entries)
# Set TEST_MODE = True in the script
python scrape_gradcafe_final.py

# For full collection (30,000 entries)
# Set TEST_MODE = False in the script
# This will take several hours
python scrape_gradcafe_final.py
```
