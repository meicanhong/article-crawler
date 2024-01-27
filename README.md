# ArticleCrawler

ArticleCrawler is a scalable, automated crawler designed to extract and parse articles from websites. It uses the Playwright library for web scraping, BeautifulSoup for HTML parsing, and stores the raw HTML data in a MongoDB collection.

## Features

- Multithreaded crawling with customizable concurrency level.
- Configurable maximum number of pages to crawl.
- Configurable request timeout.
- Option to only crawl pages from the same domain as the start URL.
- Ability to include or exclude URLs based on regex patterns.
- Configurable maximum recursion depth for the crawler.
- Configurable minimum length of a URL to be considered for crawling.
- Stores raw HTML data and parse data in a MongoDB collection.

## Dependencies

- Python
- Playwright
- BeautifulSoup
- courlan
- MongoDB

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright

```bash 
playwright install
```

### 3. Start MongoDB

```bash
docker-compose up -d
```

### 4. Run the Crawler

```python
from article_crawler import ArticleCrawler

url = 'https://followin.io/en'
crawler = ArticleCrawler(start_url=url, max_pages=5)
crawler.run()
```
In the above example, the crawler starts from the URL 'https://followin.io/en' and crawls a maximum of 5 pages. 

## Configuration
## Configuration

The `ArticleCrawler` class constructor takes the following arguments:

- `start_url` (str): The starting URL for the crawler.
- `max_pages` (int, optional): The maximum number of pages to crawl. Defaults to 1.
- `request_timeout` (int, optional): The maximum time to wait for a page to load, in seconds. Defaults to 60.
- `concurrency` (int, optional): The number of concurrent threads to use for crawling. Defaults to 1.
- `crypto_only_same_domain` (bool, optional): If True, only crawl pages from the same domain as the start_url. Defaults to False.
- `include_urls` (str, optional): A regex pattern of URLs to include in the crawl. Defaults to None.
- `exclude_urls` (str, optional): A regex pattern of URLs to exclude from the crawl. Defaults to None.
- `max_recursion_depth` (int, optional): The maximum depth of recursion for the crawler. Defaults to 2.
- `url_min_length` (int, optional): The minimum length of a URL to be considered for crawling. Defaults to 15.