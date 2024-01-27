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
from article_parser import ArticleParser
from constant import PROJECT_PATH
from factory import mongo_client

logging.basicConfig(level=logging.INFO)


class Tls(threading.local):
    def __init__(self):
        self.playwright = sync_playwright().start()
        print("Create playwright instance in Thread", threading.current_thread().name)

    def __del__(self):
        self.playwright.stop()
        print("Stop playwright instance in Thread", threading.current_thread().name)


class ArticleCrawler:

    def __init__(self, url, type='article', max_sites=50, max_links_per_page=10, timeout=60, crawler_only_internal=True,
                 match_url=None, black_website=None, max_recursion_depth=2):
        self.tls = Tls()
        self.url = url
        self.type = type
        self.max_sites = max_sites
        self.max_links_per_page = max_links_per_page
        self.max_recursion_depth = max_recursion_depth
        self.visited_urls = set()
        self.url_queue = Queue()
        self.sites_count = 0
        self.lock = threading.Lock()
        self.timeout = timeout
        self.crawler_only_internal = crawler_only_internal
        self.match_url = match_url
        self.black_website = black_website
        self.article_parser = ArticleParser()
        self.raw_data_collection = mongo_client["ai_qa"]["crawler_raw_data"]

    def run(self):
        futures = []
        self.url_queue.put((self.url, 1))  # Add depth information to the queue
        with ThreadPoolExecutor(max_workers=1) as executor:
            while self.sites_count < self.max_sites:
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
            if url in self.visited_urls:
                return
            if self.sites_count >= self.max_sites or depth > self.max_recursion_depth:
                return
            logging.info(f"Processing {url}")
            # 下载网页
            content = self.download_url(url)
            # 记录已经访问过的URL
            self.visited_urls.add(url)
            # 将当前页面中的链接加入到队列中
            links = self.extract_links(html=content, url=url)
            for link in links:
                self.add_urls((link, depth + 1))
            # 保存原始的HTML
            self.save_raw_html(url, content)
            # 解析网页
            doc = self.article_parser.parse_html(url, content)
            # 黑名单过滤, 不保存黑名单中的网站
            if self.black_website is not None:
                black_pattern = re.compile(self.black_website)
                if black_pattern.match(url):
                    return None
            # 保存解析后的数据
            result = doc.update_one()
            if result is not None:
                self.increase_sites_count()
        except Exception as e:
            logging.error(e)
            raise e

    def download_url(self, current_url):
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

            page.goto(current_url, timeout=self.timeout * 1000, wait_until='domcontentloaded')

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
        tags_to_remove = ['nav', 'footer', 'script', 'style', 'noscript', 'svg']
        # 移除指定的标签
        for tag in tags_to_remove:
            for t in soup.find_all(tag):
                t.extract()
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
            if self.crawler_only_internal and is_external(href, self.url):
                continue
            if href in self.visited_urls:
                continue
            if self.match_url is not None:
                url_pattern = re.compile(self.match_url)
                if not url_pattern.match(href):
                    continue
            # path长度小于15，大概率不是文章
            url_obj = urlparse(href)
            if url_obj.path is None or len(url_obj.path) < 10:
                continue
            urls.append(href)

        urls = list(set(urls))
        urls.sort(key=lambda x: len(x), reverse=True)
        urls = urls[:self.max_links_per_page]

        logging.info(f"Crawled Queue:{self.url_queue.qsize()}, Success: {self.sites_count}")

        return urls

    def add_urls(self, url):
        if self.sites_count >= self.max_sites:
            return
        if url in self.visited_urls:
            return
        if self.url_queue.qsize() >= self.max_sites * 2:
            return
        self.url_queue.put(url, block=False)

    def increase_sites_count(self):
        with self.lock:
            self.sites_count += 1


if __name__ == '__main__':
    url = 'https://followin.io/en'
    crawler = ArticleCrawler(url=url, type='news', max_sites=5, max_links_per_page=5,
                             timeout=60, crawler_only_internal=False)
    crawler.run()
