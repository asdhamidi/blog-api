from flask import Blueprint, jsonify, request
from models import users_collection
from bson.objectid import ObjectId
from config import JWT_SECRET
from models import codes_collection
import bcrypt
import datetime
import jwt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
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

@auth_bp.route('/login', methods=['POST'])
def login():
    login_data = request.json
    username = login_data.get("username")
    password = login_data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    user = users_collection.find_one({"username": username})
    if user and bcrypt.checkpw(password.encode('utf-8'), user["password"]):
        token = jwt.encode({"username": username, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, JWT_SECRET, algorithm="HS256")
        return jsonify({"message": "Login successful", "token": token}), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401
    
