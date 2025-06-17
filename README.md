# LinkedIn Company Posts Scraper

A Python script to scrape posts, likes, comments, shares, images, and videos from a LinkedIn company page using Selenium.

## Features

- Logs into LinkedIn with your credentials
- Scrapes posts from a company’s LinkedIn page
- Extracts post text, likes, comments, shares, images, and videos
- Saves results to a JSON file
- Configurable scrolls, headless mode, and comment limits

## Requirements

- Python 3.7+
- Google Chrome browser
- [ChromeDriver](https://sites.google.com/chromium.org/driver/) (compatible with your Chrome version)
- Python packages:
  - `selenium`

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Setup

1. Download the correct version of ChromeDriver and ensure it is in your system PATH or the same directory as your script.
2. Update the `config` dictionary in `scraper.py` with your LinkedIn email and password.

## Usage

```bash
python scraper.py
```

The script will:

- Log in to LinkedIn
- Scrape posts from the specified company page (update `company_url` in the script)
- Save the results to a JSON file named like `companyname_posts_YYYYMMDD_HHMMSS.json`

## Configuration

You can adjust the following parameters in the `config` dictionary in `scraper.py`:

- `email`: Your LinkedIn email
- `password`: Your LinkedIn password
- `headless`: Run browser in headless mode (`True`/`False`)
- `window_size`: Browser window size (width, height)
- `num_scrolls`: Number of times to scroll the page to load posts
- `scroll_pause`: Time to pause between scrolls (seconds)
- `max_comments`: Maximum number of comments to extract per post

## Example

```python
config = {
    "email": "your_email@example.com",
    "password": "your_password",
    "headless": False,
    "window_size": (1200, 900),
    "num_scrolls": 12,
    "scroll_pause": 2.5,
    "max_comments": 15
}

company_url = "https://www.linkedin.com/company/company-name/posts/"
```

## Output

- JSON file with all scraped posts and their details.

## Notes

- This script is for educational and personal use only. Scraping LinkedIn may violate their terms of service.
- Make sure to use your own credentials and do not share them.
- LinkedIn’s UI may change, which can break the scraper. Update selectors as needed.

## License

See [LICENSE](LICENSE)