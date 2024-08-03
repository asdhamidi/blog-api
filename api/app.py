from flask import Flask, jsonify, request
from bson.objectid import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv
from functools import wraps
from flask_cors import CORS 
import datetime
import bcrypt
import random
import jwt
import os

load_dotenv()

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

mongodb_uri = os.getenv("MONGODB_URI")
blog_db_name = os.getenv('BLOG_DB')
jwt_secret = os.getenv("JWT_SECRET") 

if not mongodb_uri or not blog_db_name:
    raise ValueError("MONGODB_URI and BLOG_DB must be set in the environment variables.")

# Connect to MongoDB
client = MongoClient(mongodb_uri)
db = client[blog_db_name] 
posts_collection = db['posts']
users_collection = db['users']
codes_collection = db['codes']

# Home route.
@app.route('/')
def home():
    return """
    Welcome to my Blog API!

    For full documentation and usage details, please visit:
    https://github.com/asdhamidi/blog-api/blob/main/README.md

    Happy trails!
    """

# Decorator for route protection.
def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = request.headers.get('Authorization')[7:]
        if not token:
            return jsonify({"message": "Token is missing!"}), 401
        
        try:
            jwt.decode(token, jwt_secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 401
        
        return f(*args, **kwargs)
    return decorator


# Authentication endpoints
@app.route('/register', methods=['POST'])
def register():
    user_data = request.json
    username = user_data.get("username")
    password = user_data.get("password")
    register_code = user_data.get("register_code")
    
    if not username or not password or not register_code:
        return jsonify({"message": "Username, password, and registration code are required"}), 400

    if users_collection.find_one({"username": username}):
        return jsonify({"message": "Username already exists"}), 400

    # Verify the registration code
    code_entry = codes_collection.find_one({"code": register_code})
    if not code_entry:
        return jsonify({"message": "Invalid registration code"}), 400

    # Hash the password and store the new user
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    new_user = {
        "_id": ObjectId(),
        "username": username,
        "password": hashed_password,
        "created_at": datetime.datetime.now().strftime("%B %-d, %Y - %I:%M %p")
    }

    users_collection.insert_one(new_user)
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    login_data = request.json
    username = login_data.get("username")
    password = login_data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    user = users_collection.find_one({"username": username})
    if user and bcrypt.checkpw(password.encode('utf-8'), user["password"]):
        token = jwt.encode({"username": username, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, jwt_secret, algorithm="HS256")
        return jsonify({"message": "Login successful", "token": token}), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401
    

@app.route('/generate_code', methods=['POST'])
@token_required
def generate_code():
    new_code = {
        "_id": ObjectId(),
        "code": str(random.randint(100000, 999999)),  # Generate a random 6-byte code
        "created_at": datetime.datetime.now().strftime("%B %-d, %Y - %I:%M %p")
    }
    codes_collection.insert_one(new_code)
    return jsonify({"message": "Registration code generated", "code": new_code["code"]}), 201


# Public endpoints
@app.route('/posts', methods=['GET'])
def get_posts():
    posts = list(posts_collection.find({}, {'_id': 1, 'title': 1, 'author': 1, 'date': 1})) 
    for post in posts:
        post['_id'] = str(post['_id']) 
    return jsonify(posts)

@app.route('/posts/<string:id>', methods=['GET'])
def get_post_by_id(id):
    post = posts_collection.find_one({'_id': ObjectId(id)}, {'_id': 1, 'title': 1, 'content': 1, 'author': 1, 'date': 1})
    
    if post:
        post['_id'] = str(post['_id'])
        return jsonify(post)
    else:
        return jsonify({"message": "Post not found"}), 404

# Protected endpoints
@app.route('/posts', methods=['POST'])
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

@app.route('/posts/<string:id>', methods=['PUT'])
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

@app.route('/posts/<string:id>', methods=['DELETE'])
@token_required
def delete_post(id):
    post_id = ObjectId(id)
    
    result = posts_collection.delete_one({"_id": post_id})
    
    if result.deleted_count > 0:
        return jsonify({"message": "Post deleted successfully"})
    else:
        return jsonify({"message": "Post not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)