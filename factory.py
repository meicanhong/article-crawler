import pymongo
from openai import OpenAI

from config import project_config

mongo_client = pymongo.MongoClient(project_config.mongodb_url)

openai_client = OpenAI(api_key=project_config.openai_api_key)