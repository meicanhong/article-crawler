import pymongo
from config import project_config

mongo_client = pymongo.MongoClient(project_config.mongodb_url)