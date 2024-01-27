import logging
import re
import threading
from concurrent.futures import wait, FIRST_COMPLETED
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from queue import Queue
from time import sleep
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from courlan import validate_url, scrub_url, clean_url, is_external
from playwright.sync_api import sync_playwright
from article_parser import parse_html, remove_irrelevant_html_elements
from constant import PROJECT_PATH
from factory import mongo_client

logging.basicConfig(level=logging.INFO)


class PlaywrightInstance(threading.local):
    def __init__(self):
        self.playwright = sync_playwright().start()
        print("Create playwright instance in Thread", threading.current_thread().name)

    def __del__(self):
        self.playwright.stop()
        print("Stop playwright instance in Thread", threading.current_thread().name)


class ArticleCrawler:
    def __init__(self, start_url, max_pages=1, request_timeout=60, concurrency=1, crypto_only_same_domain=False,
                 include_urls=None, exclude_urls=None, max_recursion_depth=2, url_min_length=15):
        """
        Initializes the ArticleCrawler object.

        Args:
            start_url (str): The starting URL for the crawler.
            max_pages (int, optional): The maximum number of pages to crawl. Defaults to 1.
            request_timeout (int, optional): The maximum time to wait for a page to load, in seconds. Defaults to 60.
            concurrency (int, optional): The number of concurrent threads to use for crawling. Defaults to 1.
            crypto_only_same_domain (bool, optional): If True, only crawl pages from the same domain as the start_url. Defaults to False.
            include_urls (str, optional): A regex pattern of URLs to include in the crawl. Defaults to None.
            exclude_urls (str, optional): A regex pattern of URLs to exclude from the crawl. Defaults to None.
            max_recursion_depth (int, optional): The maximum depth of recursion for the crawler. Defaults to 2.
            url_min_length (int, optional): The minimum length of a URL to be considered for crawling. Defaults to 15.
        """

        self.tls = PlaywrightInstance()  # Instance of Playwright for web scraping
        self.start_url = start_url  # The starting URL for the crawler
        self.max_pages = max_pages  # The maximum number of pages to crawl
        self.request_timeout = request_timeout  # The maximum time to wait for a page to load, in seconds
        self.concurrency = concurrency  # The number of concurrent threads to use for crawling
        self.crypto_only_same_domain = crypto_only_same_domain  # If True, only crawl pages from the same domain as the start_url
        self.include_urls = include_urls  # A regex pattern of URLs to include in the crawl
        self.exclude_urls = exclude_urls  # A regex pattern of URLs to exclude from the crawl
        self.max_recursion_depth = max_recursion_depth  # The maximum depth of recursion for the crawler
        self.url_min_length = url_min_length  # The minimum length of a URL to be considered for crawling

        self.visited_urls = set()  # A set of URLs that have already been visited
        self.url_queue = Queue()  # A queue of URLs to be visited
        self.success_page_count = 0  # The number of pages that have been successfully crawled
        self.lock = threading.Lock()  # A lock for thread-safe operations
        self.raw_data_collection = mongo_client["ai_qa"]["crawler_raw_data"]  # MongoDB collection for storing raw data

    def run(self):
        futures = []
        self.url_queue.put((self.start_url, 1))
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            while self.success_page_count < self.max_pages:
                try:
                    current_url, depth = self.url_queue.get_nowait()
                except:
                    current_url, depth = None, 0
                if current_url:
                    future = executor.submit(self.process_single_url, current_url, depth)
                    futures.append(future)
                    continue
                done, not_done = wait(futures, timeout=3, return_when=FIRST_COMPLETED)
                if len(futures) == 0:
                    break
                for future in done:
                    future.result()
                    futures.remove(future)
                sleep(5)

    def process_single_url(self, url, depth):
        try:
            if url in self.visited_urls or self.success_page_count >= self.max_pages or depth > self.max_recursion_depth:
                return
            logging.info(f"Processing {url}, Success crawled: {self.success_page_count}, "
                         f"Total crawled: {len(self.visited_urls)}")
            content = self.download_pages(url)
            if content is None:
                return
            content = remove_irrelevant_html_elements(content)
            links = self.extract_links(html=content, url=url)
            for link in links:
                self.add_queue_urls(link, depth + 1)
            self.save_raw_html(url, content)
            if self.is_exclude_url(url):
                return
            doc = parse_html(url, content)
            # 保存解析后的数据
            result = doc.update_one()
            if result is not None:
                self.increase_sites_count()
        except Exception as e:
            logging.error(e)
            raise e

    def download_pages(self, current_url):
        browser = None
        context = None
        page = None
        try:
            browser = self.tls.playwright.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']  # 防止被检测
            )
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 "
                           "Safari/537.36"
            )
            # 添加反爬插件
            context.add_init_script(path=f"{PROJECT_PATH}/stealth.min.js")

            page = context.new_page()

            page.goto(current_url, timeout=self.request_timeout * 1000, wait_until='domcontentloaded')

            scroll_height = 10000  # 替换为您想要的滚动高度
            scroll_height_unit = 400  # 替换为您想要的滚动高度单位
            current_height = 0
            for i in range(0, scroll_height, scroll_height_unit):
                current_height += scroll_height_unit
                # 滚动到指定高度
                page.evaluate(f"window.scrollTo(0, {current_height});")
                # 等待一段时间
                page.wait_for_timeout(200)

            content = page.content()
            return content
        except Exception as e:
            if str(e).__contains__('Timeout'):
                logging.error(f"Timeout downloading URL '{current_url}': {e}")
                return None
            logging.error(f"Error downloading URL '{current_url}': {e}")
            raise e
        finally:
            self.add_visited_url(current_url)
            if page is not None:
                page.close()
            if context is not None:
                context.close()
            if browser is not None:
                browser.close()

    def save_raw_html(self, url, content):
        doc = {
            "url": url,
            "content": content,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        self.raw_data_collection.update_one(filter={"url": url}, update={"$set": doc},
                                            upsert=True)

    def extract_links(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')
        urls = []
        for link in soup.find_all('a'):
            href: str = link.get('href')
            if href is None:
                continue
            if href.startswith('/'):
                href = urljoin(url, href)
            if not validate_url(href)[0]:
                continue
            if href.__contains__('youtube.com') or href.__contains__('png') or href.__contains__('jpg'):
                continue
            href = scrub_url(href)
            href = clean_url(href)
            urls.append(href)

        urls = list(set(urls))
        urls.sort(key=lambda x: len(x), reverse=True)
        return urls

    def add_queue_urls(self, url, depth):
        if self.success_page_count >= self.max_pages or url in self.visited_urls:
            return
        if self.url_queue.qsize() >= self.max_pages * 2:
            return
        if self.crypto_only_same_domain and is_external(url, self.start_url):
            return
        if self.include_urls is not None:
            url_pattern = re.compile(self.include_urls)
            if not url_pattern.match(url):
                return
        # path长度小于15，大概率不是文章
        url_obj = urlparse(url)
        if url_obj.path is None or len(url_obj.path) < self.url_min_length:
            return
        self.url_queue.put((url, depth), block=False)

    def is_exclude_url(self, url):
        if self.exclude_urls is None:
            return False
        black_pattern = re.compile(self.exclude_urls)
        if black_pattern.match(url):
            return True
        return False

    def increase_sites_count(self):
        with self.lock:
            self.success_page_count += 1

    def add_visited_url(self, url):
        with self.lock:
            self.visited_urls.add(url)


if __name__ == '__main__':
    url = 'https://followin.io/en'
    crawler = ArticleCrawler(start_url=url, max_pages=5)
    crawler.run()
