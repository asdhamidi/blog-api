from flask import Blueprint, jsonify, request
from bson.objectid import ObjectId
from models import posts_collection
from decorators import token_required
import datetime

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('/posts', methods=['GET'])
def get_posts():
    posts = list(posts_collection.find({}, {'_id': 1, 'title': 1, 'author': 1, 'date': 1})) 
    for post in posts:
        post['_id'] = str(post['_id']) 
    return jsonify(posts)

@posts_bp.route('/posts/<string:id>', methods=['GET'])
def get_post_by_id(id):
    post = posts_collection.find_one({'_id': ObjectId(id)}, {'_id': 1, 'title': 1, 'content': 1, 'author': 1, 'date': 1})
    
    if post:
        post['_id'] = str(post['_id'])
        return jsonify(post)
    else:
        return jsonify({"message": "Post not found"}), 404

@posts_bp.route('/posts', methods=['POST'])
@token_required
def create_post():
    post_data = request.json

    new_post = {
        "_id": ObjectId(),
        "title": post_data.get("title"),
        "content": post_data.get("content"),
        "date": datetime.datetime.now().strftime("%B %-d, %Y - %I:%M %p"),
        "author": post_data.get("author")
    }

    posts_collection.insert_one(new_post)
    new_post["_id"] = str(new_post["_id"])
    
    return jsonify({"message": "Post created successfully", "post": new_post}), 201

@posts_bp.route('/posts/<string:id>', methods=['PUT'])
@token_required
def update_post(id):
    post_data = request.json
    post_id = ObjectId(id)
    post = posts_collection.find_one({'_id': post_id}, {'_id': 1, 'title': 1, 'content': 1, 'author': 1, 'date': 1})
    
    if not post:
        return jsonify({"message": "Post not found"}), 404

    updated_post = {
        "title": post_data.get("title", post['title']),
        "content": post_data.get("content", post['content']),
        "date": datetime.datetime.now().strftime("%B %-d, %Y - %I:%M %p")
    }

    result = posts_collection.update_one({"_id": post_id}, {"$set": updated_post})

    if result.matched_count == 0:
        return jsonify({"message": "No post updated, it may not exist"}), 404

    updated_post['_id'] = str(post_id)
    return jsonify({"message": "Post updated successfully", "post": updated_post}), 200

@posts_bp.route('/posts/<string:id>', methods=['DELETE'])
@token_required
def delete_post(id):
    post_id = ObjectId(id)
    
    result = posts_collection.delete_one({"_id": post_id})
    
    if result.deleted_count > 0:
        return jsonify({"message": "Post deleted successfully"})
    else:
        return jsonify({"message": "Post not found"}), 404