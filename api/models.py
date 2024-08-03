from pymongo import MongoClient
from config import MONGODB_URI, BLOG_DB_NAME

client = MongoClient(MONGODB_URI)
db = client[BLOG_DB_NAME]

posts_collection = db['posts']
users_collection = db['users']
codes_collection = db['codes']
