import logging
from urllib.parse import urlparse

import pymongo
from feapder import UpdateItem
from unstructured.cleaners.core import clean



# import feapder.pipelines.mongo_pipeline.MongoPipeline

class BaseETLItem(UpdateItem):
    mongo_client = pymongo.MongoClient('mongodb://localhost:27017')
    __unique_key__ = ["website_url"]

    def __init__(self, collection_name=None):
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
        self.collection = self.mongo_client["ai_qa"][collection_name]

    def update_one(self):
        try:
            self.verify()
            self.clean()
            self.collection.update_one(filter={"website_url": self.website_url}, update={"$set": self.doc_to_dict()}, upsert=True)
        except Exception as e:
            logging.error(f'update_one error: {e}')

    def verify(self):
        if (self.website is None or self.website_url is None
                or self.contents is None or self.source is None or self.created_at is None or self.updated_at is None
                or self.published_at is None):
            raise ValueError("website, website_url, contents, source, created_at, updated_at, published_at can't be "
                             "None")
        if self.contents == '':
            raise ValueError("contents can't be empty")

    def clean(self):
        try:
            contents = self.contents
            for content in contents:
                if content['type'] == 'text':
                    content['content'] = clean(content['content'], bullets=True, dashes=True)
            self.contents = contents

            url = self.website_url
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            self.website = domain

        except Exception as e:
            logging.error(f'clean error: {e}, contents: {self.contents}')

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