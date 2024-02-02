import json
import logging
from datetime import datetime
import trafilatura
from bs4 import BeautifulSoup
from base_etl_item import BaseETLItem
from util.openai_util import chat_response_dict


def parse_html(url: str, content: str):
    extracted_data = trafilatura.bare_extraction(filecontent=content, include_comments=True, include_images=True)
    if extracted_data is None:
        text = html_to_txt(content)
        doc = BaseETLItem()
        doc.website = url
        doc.website_url = url
        doc.contents = [{"type": "text", "content": text}]
        return [doc]

    title = extracted_data.get('title', '')
    author = extracted_data.get('author', '')
    text = extracted_data.get('text', '')
    if text == '' or len(text) < 5:
        text = html_to_txt(content)
    description = extracted_data.get('description', '')
    published_date = extracted_data.get('date', '')
    language = extracted_data.get('language', '')
    tags = extracted_data.get('tags', [])

    doc = BaseETLItem()
    doc.website = url
    doc.website_url = url
    doc.headline = title
    doc.description = description
    doc.author = author
    doc.language = language
    doc.tags = tags
    doc.created_at = datetime.utcnow()
    doc.updated_at = datetime.utcnow()
    doc.published_at = published_date

    if html_is_table(content):
        table_data = parse_table(content)
        if table_data and len(table_data) > 0:
            doc.contents = [{"type": "table", "content": table_data}]

    if doc.contents is None or len(doc.contents) == 0:
        doc.contents = [{"type": "text", "content": text}]

    return doc


def parse_table(html):
    try:
        html = html_to_txt(html)
        return extract_json_data(html)
    except Exception as e:
        logging.error(f"Error parsing table: {e}")
        return None


def extract_json_data(html):
    try:
        content = f"""Given a string containing HTML content, please help me extract the JSON data.
If there is table data in HTML, please help me extract the JSON data of the table from it. Do not lose any data or include any HTML tags. Try to retain the key value of the original content and do not merge similar keys privately.
Here is my input:
{html}
The returned data structure must be, and the extracted data must be in an array
{{"data":[]}}
        """
        result = chat_response_dict(content)
        return json.dumps(result)
    except Exception as e:
        logging.error(f"Error extracting JSON data from HTML: {e}")
        return None


def html_to_txt(input_html):
    soup = BeautifulSoup(input_html, 'html.parser')
    # 只保留文本内容
    return soup.get_text()


def remove_irrelevant_html_elements(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')

    # List of tags to remove
    tags_to_remove = ['nav', 'footer', 'script', 'style', 'noscript', 'svg', 'aside', 'header']

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


def html_is_table(html: str):
    html = html_to_txt(html)
    # text 中逗号和句号的数量
    nums_comma = html.count(',')
    html_len = len(html)
    threshold = html_len * 0.001
    # 向上取整
    threshold = int(threshold)
    # 如果文本长度大于 50 个字符并且逗号和句号的数量大于 5 个，那么就不是表格
    return not (len(html) > 50 and nums_comma > threshold)
