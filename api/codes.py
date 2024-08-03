from flask import Blueprint, jsonify
from models import codes_collection
from decorators import token_required
import datetime
import random
from bson.objectid import ObjectId

codes_bp = Blueprint('codes', __name__)

@codes_bp.route('/generate_code', methods=['POST'])
@token_required
def generate_code():
    new_code = {
        "_id": ObjectId(),
        "code": str(random.randint(100000, 999999)),  # Generate a random 6-byte code
        "created_at": datetime.datetime.now().strftime("%B %-d, %Y - %I:%M %p")
    }
    codes_collection.insert_one(new_code)
    return jsonify({"message": "Registration code generated", "code": new_code["code"]}), 201