from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
import os
from dotenv import load_dotenv
from flask_cors import CORS 

load_dotenv()

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

mongodb_uri = os.getenv("MONGODB_URI")
blog_db_name = os.getenv('BLOG_DB')

if not mongodb_uri or not blog_db_name:
    raise ValueError("MONGODB_URI and BLOG_DB must be set in the environment variables.")

# Connect to MongoDB
client = MongoClient(mongodb_uri)
db = client[blog_db_name] 
posts_collection = db['posts']

@app.route('/')
def home():
    return "Home of asad's blog API!"

@app.route('/posts', methods=['GET'])
def get_posts():
    posts = list(posts_collection.find({}, {'_id': 1, 'title': 1, 'author': 1, 'date': 1})) 
    for post in posts:
        post['_id'] = str(post['_id'])  # Convert ObjectId to string
    return jsonify(posts)

@app.route('/posts/<string:id>', methods=['GET'])
def get_post_by_id(id):
    post = posts_collection.find_one({'_id': ObjectId(id)}, {'_id': 1, 'title': 1, 'content': 1, 'author': 1, 'date': 1})
    
    if post:
        post['_id'] = str(post['_id'])
        return jsonify(post)
    else:
        return jsonify({"message": "Post not found"}), 404

@app.route('/post', methods=['POST'])
def create_post():
    post_data = request.json

    new_post = {
        "_id": ObjectId(),
        "title": post_data.get("title"),
        "content": post_data.get("content"),
        "date": datetime.datetime.now().strftime("%d-%m-%Y"),
        "author": post_data.get("author")
    }

    posts_collection.insert_one(new_post)
    new_post["_id"] = str(new_post["_id"])
    
    return jsonify({"message": "Post created successfully", "post": new_post}), 201

@app.route('/post/<string:id>', methods=['PUT'])
def update_post(id):
    post_data = request.json
    post = posts_collection.find_one({'_id': ObjectId(id)}, {'_id': 1, 'title': 1, 'content': 1, 'author': 1, 'date': 1})
    
    updated_post = {
        "title": post_data.get("title", post['title']),
        "content": post_data.get("content", post['content']),
        "date": datetime.datetime.now().strftime("%d-%m-%Y")  # or use `post['date']` to keep the original date
    }
    posts_collection.update_one({"_id": id}, {"$set": updated_post})

    return jsonify({"message": "Post created successfully", "post": updated_post}), 200

@app.route('/post/<string:id>', methods=['DELETE'])
def delete_post(id):
    post_id = ObjectId(id)
    
    result = posts_collection.delete_one({"_id": post_id})
    
    if result.deleted_count > 0:
        return jsonify({"message": "Post deleted successfully"})
    else:
        return jsonify({"message": "Post not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)