import logging
import re
import threading
from concurrent.futures import wait, FIRST_COMPLETED
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from queue import Queue
from time import sleep
from urllib.parse import urljoin, urlparse
import pymongo
import trafilatura
from bs4 import BeautifulSoup
from courlan import validate_url, scrub_url, clean_url, is_external
from htmldate import find_date
from newspaper import Article
from playwright.sync_api import sync_playwright

from base_etl_item import BaseETLItem
from config import project_config
from constant import PROJECT_PATH

logging.basicConfig(level=logging.INFO)

mongo_client = pymongo.MongoClient(project_config.mongodb_url)


class Tls(threading.local):
    def __init__(self):
        self.playwright = sync_playwright().start()
        print("Create playwright instance in Thread", threading.current_thread().name)


class ArticleCrawler:

    def __init__(self, url, type='article', max_sites=50, max_links_per_page=10, timeout=60, crawler_only_internal=True,
                 match_url=None, black_website=None):
        self.tls = Tls()
        self.url = url
        self.type = type
        self.max_sites = max_sites
        self.max_links_per_page = max_links_per_page
        self.visited_urls = set()
        self.url_queue = Queue()
        self.sites_count = 0
        self.lock = threading.Lock()
        self.timeout = timeout
        self.crawler_only_internal = crawler_only_internal
        self.match_url = match_url
        self.black_website = black_website
        self.etl_data_collection_name = 'crawler_etl_data'
        self.raw_data_collection = mongo_client["ai_qa"]["crawler_raw_data"]

    def run(self):
        futures = []
        self.url_queue.put(self.url)
        with ThreadPoolExecutor(max_workers=1) as executor:
            while self.sites_count < self.max_sites:
                try:
                    current_url = self.url_queue.get_nowait()
                except:
                    current_url = None
                if current_url:
                    future = executor.submit(self.process_single_url, current_url)
                    futures.append(future)
                else:
                    done, not_done = wait(futures, timeout=3, return_when=FIRST_COMPLETED)
                    for future in done:
                        future.result()
                        futures.remove(future)
                    sleep(5)

    def process_single_url(self, url):
        try:
            if url in self.visited_urls:
                return
            if self.sites_count >= self.max_sites:
                return
            logging.info(f"Processing {url}")
            # 下载网页
            content = self.download_url(url)
            # 记录已经访问过的URL
            self.visited_urls.add(url)
            # 将当前页面中的链接加入到队列中
            links = self.extract_links(html=content, url=url)
            for link in links:
                self.add_urls(link)
            # 保存原始的HTML
            self.save_raw_html(url, content)
            # 解析网页
            doc = self.parse_website(url, content)
            # 黑名单过滤, 不保存黑名单中的网站
            black_pattern = re.compile(self.black_website)
            if black_pattern.match(url):
                return None
            # 保存解析后的数据
            doc.update_one()
            self.increase_sites_count()
        except Exception as e:
            logging.error(e)
            raise e

    def download_url(self, current_url):
        browser = self.tls.playwright.chromium.launch(
            headless=False,
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

        scroll_height = 30000  # 替换为您想要的滚动高度
        scroll_height_unit = 10000  # 替换为您想要的滚动高度单位
        current_height = 0
        for i in range(0, scroll_height, scroll_height_unit):
            current_height += scroll_height_unit
            # 滚动到指定高度
            page.evaluate(f"window.scrollTo(0, {current_height});")
            # 等待一段时间
            wait_time = 1000  # 替换为您想要等待的时间（毫秒）
            page.wait_for_timeout(wait_time)

        content = page.content()
        page.close()
        browser.close()
        return content

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

    def parse_website(self, url, content):
        article = Article(url)
        article.download(content)
        article.parse()
        published_date = article.publish_date
        if published_date is None:
            published_date = find_date(htmlobject=content, outputformat="%Y-%m-%d %H:%M:%S")

        text = trafilatura.extract(filecontent=content, include_comments=True, include_images=False)
        metadata = trafilatura.extract_metadata(filecontent=content)
        tags = list(article.tags)
        if tags is None or len(tags) == 0:
            tags = metadata.tags

        author = metadata.author
        if author is None or len(author) == 0:
            if metadata.author is not None:
                author = article.author
            else:
                element = BeautifulSoup(content, 'html.parser').find('span', class_='text-text1 text-lg font-medium')
                if element is not None:
                    author = element.text

        doc = BaseETLItem(collection_name=self.etl_data_collection_name)
        doc.website = url
        doc.website_url = url
        doc.headline = article.title
        doc.description = article.text[:200]
        doc.contents = [{"type": "text", "content": text}]
        doc.author = author
        doc.source = self.type
        doc.language = article.meta_lang
        doc.tags = tags
        doc.created_at = datetime.utcnow()
        doc.updated_at = datetime.utcnow()
        doc.published_at = published_date
        return doc

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
    crawler = ArticleCrawler(url=url, type='news', max_sites=100, max_links_per_page=999,
                             timeout=60, crawler_only_internal=False)
    crawler.run()
