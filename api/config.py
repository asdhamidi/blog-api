import os

MONGODB_URI = os.getenv("MONGODB_URI")
BLOG_DB_NAME = os.getenv('BLOG_DB')
JWT_SECRET = os.getenv("JWT_SECRET")

if not MONGODB_URI or not BLOG_DB_NAME:
    raise ValueError("MONGODB_URI and BLOG_DB must be set in the environment variables.")
