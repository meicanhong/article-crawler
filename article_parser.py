from datetime import datetime
import trafilatura
from bs4 import BeautifulSoup
from htmldate import find_date
from newspaper import Article
from base_etl_item import BaseETLItem


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
