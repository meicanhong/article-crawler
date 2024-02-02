import logging
import re
from urllib.parse import urlparse
from dateutil.parser import parser
from unstructured.cleaners.core import clean
from factory import mongo_client


class BaseETLItem:
    def __init__(self):
        self.subtype = None
        self.created_at = None
        self.updated_at = None
        self.name = None
        self.website = None
        self.website_url = None
        self.headline = None
        self.subheadline = ''
        self.description = None
        self.tags = []
        self.related = []
        self.contents = None
        self.author = None
        self.published_at = None
        self.source = None
        self.language = None
        self.collection = mongo_client["ai_qa"]["crawler_raw_data"]

    def update_one(self):
        try:
            self.verify()
            self.clean()

            # Try to get the document from the database
            doc = self.collection.find_one({"website_url": self.website_url})

            # If the document exists, get its created_at
            if doc is not None:
                self.created_at = doc.get('created_at')

            doc = self.collection.update_one(filter={"website_url": self.website_url},
                                             update={"$set": self.doc_to_dict()},
                                             upsert=True)
            logging.info(f'update_one success: {self.website_url} {self.headline} {self.published_at}')
            return doc
        except Exception as e:
            logging.error(f'{self.website_url} update_one error: {e}')

    def verify(self):
        fields_to_check = [self.website, self.website_url, self.contents, self.created_at, self.updated_at]
        if not all(fields_to_check) or self.contents == '':
            raise ValueError(
                f"{self.website_url}: website, website_url, contents, created_at, updated_at "
                f"can't be None or empty")
        if self.contents == '':
            raise ValueError(f"{self.website_url} contents can't be empty")

    def clean(self):
        try:
            contents = self.contents
            for content in contents:
                if content['type'] == 'text':
                    content['content'] = clean(str(content['content']), bullets=True, dashes=True)
            self.contents = contents

            # website 变为域名
            url = self.website_url
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            self.website = domain

            # published_at 变为datetime
            if type(self.published_at) == str:
                self.published_at = parser().parse(self.published_at)

            # author 变为字符串
            author = self.author
            if type(author) == list:
                author = ', '.join(author)
            match_result = re.search(r'([^\s]+)', author)
            if match_result is not None:
                author = match_result.group(1)
            author = clean(author, bullets=True, dashes=True)
            self.author = author

            # tags摊平列表
            tags = self.tags
            new_tags = {item for tag in tags if isinstance(tag, (list, str)) for item in
                        (tag if isinstance(tag, list) else re.split(r'[,\s]+', tag))}
            self.tags = list(new_tags)


        except Exception as e:
            logging.error(f'{self.website_url} clean error: {e}')

    def doc_to_dict(self):
        return {
            "name": self.name,
            "website": self.website,
            "website_url": self.website_url,
            "author": self.author,
            "language": self.language,
            "headline": self.headline,
            "subheadline": self.subheadline,
            "description": self.description,
            "contents": self.contents,
            "tags": self.tags,
            "related": self.related,
            "source": self.source,
            "subtype": self.subtype,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "published_at": self.published_at,
        }
