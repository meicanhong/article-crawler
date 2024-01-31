import logging
from datetime import datetime
import trafilatura
from bs4 import BeautifulSoup
from htmldate import find_date
from htmllaundry import sanitize
from newspaper import Article
from base_etl_item import BaseETLItem
from util.openai_util import chat_response_dict


def parse_html(url: str, content: str):
    # 拷贝 content
    article = Article(url)
    article.download(content[:])
    article.parse()
    published_date = article.publish_date
    if published_date is None or published_date == '':
        published_date = find_date(htmlobject=content, outputformat="%Y-%m-%d %H:%M:%S")

    text = trafilatura.extract(filecontent=content, include_comments=True, include_images=True)
    metadata = trafilatura.extract_metadata(filecontent=content)
    if metadata:
        tags = list(article.tags)
        if tags is None or len(tags) == 0:
            tags = metadata.tags

        author = metadata.author
    else:
        tags = list(article.tags)
        author = article.authors
    if author is None or len(author) == 0:
        element = BeautifulSoup(content, 'html.parser').find('span', class_='text-text1 text-lg font-medium')
        if element is not None:
            author = element.text

    if article.title is None or article.title == '' or text is None or text == '':
        text = parse_table(content)

    doc = BaseETLItem()
    doc.website = url
    doc.website_url = url
    doc.headline = article.title
    doc.description = article.text[:200]
    doc.contents = [{"type": "text", "content": text}]
    doc.author = author
    doc.source = 'article'
    doc.language = article.meta_lang
    doc.tags = tags
    doc.created_at = datetime.utcnow()
    doc.updated_at = datetime.utcnow()
    doc.published_at = published_date
    return doc


def remove_irrelevant_html_elements(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')

    # List of tags to remove
    tags_to_remove = ['nav', 'footer', 'script', 'style', 'noscript', 'svg']

    # Remove specified tags
    for tag in tags_to_remove:
        for t in soup.find_all(tag):
            t.extract()

    # List of roles to remove
    roles_to_remove = ['alert', 'banner', 'dialog', 'alertdialog']

    # Remove elements with specified roles
    for role in roles_to_remove:
        for t in soup.select(f'[role="{role}"]'):
            t.extract()

    # Remove elements with specified attributes
    for t in soup.select('[role="region"][aria-label*="skip" i], [aria-modal="true"]'):
        t.extract()

    return str(soup)


def parse_table(html):
    html = sanitize(html)
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if attr not in ['src', 'href']:
                del tag[attr]
    html = soup.prettify()
    return extract_json_data(html)


def verify_html_contains_table(html):
    soup = BeautifulSoup(html, 'html.parser')
    # 找到 html 中 height 和 width 的数量
    height_width_count = len(soup.find_all(lambda tag: tag.has_attr('height') or tag.has_attr('width')))
    return height_width_count


def extract_json_data(html):
    try:
        content = f"""
        Given a string containing HTML content, help me extract the JSON data.
        If there is table data in HTML, please help me extract the JSON data of the table from it without missing any data or including any HTML tags.
        If the HTML content is not a table, an empty string is returned.
        Here is my input:
        {html}
        Please return JSON data.
        """
        return chat_response_dict(content)
    except Exception as e:
        logging.error(f"Error extracting JSON data from HTML: {e}")
        return None
