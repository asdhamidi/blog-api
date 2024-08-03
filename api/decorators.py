from functools import wraps
from flask import request, jsonify
import jwt
from config import JWT_SECRET

def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = request.headers.get('Authorization')[7:]
        if not token:
            return jsonify({"message": "Token is missing!"}), 401

        try:
            jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 401

        return f(*args, **kwargs)
    return decorator
