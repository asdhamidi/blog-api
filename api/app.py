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
visits_collection = db['visits']


# Home route.
@app.route('/')
def home():
    return """
    Welcome to my Blog API!

    For full documentation and usage details, please visit:
    https://github.com/asdhamidi/blog-api/blob/main/README.md

    Happy trails!
    """

@app.route('/visit', methods=['GET'])
def add_visit():
    try:
        post_data = dict(request.args)  # Use query params instead of JSON
        headers = dict(request.headers)
        
        # Extract meaningful information
        user_agent = headers.get('User-Agent', '')
        referrer = request.referrer or 'Direct'
        ip_address = request.remote_addr
        
        # Parse User-Agent for device/browser info
        device_type = 'Unknown'
        browser = 'Unknown'
        os = 'Unknown'
        
        if user_agent:
            # Simple user agent parsing (consider using a library like user-agents for production)
            ua_lower = user_agent.lower()
            
            # Device detection
            if any(mobile in ua_lower for mobile in ['mobile', 'android', 'iphone']):
                device_type = 'Mobile'
            elif 'tablet' in ua_lower:
                device_type = 'Tablet'
            else:
                device_type = 'Desktop'
            
            # Browser detection
            if 'chrome' in ua_lower and 'edg' not in ua_lower:
                browser = 'Chrome'
            elif 'firefox' in ua_lower:
                browser = 'Firefox'
            elif 'safari' in ua_lower and 'chrome' not in ua_lower:
                browser = 'Safari'
            elif 'edg' in ua_lower:
                browser = 'Edge'
            elif 'opera' in ua_lower:
                browser = 'Opera'
            
            # OS detection
            if 'windows' in ua_lower:
                os = 'Windows'
            elif 'mac os' in ua_lower or 'macos' in ua_lower:
                os = 'macOS'
            elif 'linux' in ua_lower:
                os = 'Linux'
            elif 'android' in ua_lower:
                os = 'Android'
            elif 'ios' in ua_lower or 'iphone' in ua_lower:
                os = 'iOS'
        
        # Parse referrer for source tracking
        referrer_source = 'Direct'
        referrer_domain = None
        
        if referrer and referrer != 'Direct':
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(referrer)
                referrer_domain = parsed_url.netloc
                
                # Common source classification
                if any(domain in referrer_domain for domain in ['google.', 'bing.', 'yahoo.', 'duckduckgo.']):
                    referrer_source = 'Search Engine'
                elif 'facebook.com' in referrer_domain:
                    referrer_source = 'Facebook'
                elif 'twitter.com' in referrer_domain or 'x.com' in referrer_domain:
                    referrer_source = 'Twitter'
                elif 'linkedin.com' in referrer_domain:
                    referrer_source = 'LinkedIn'
                elif 'github.com' in referrer_domain:
                    referrer_source = 'GitHub'
                elif 'youtube.com' in referrer_domain:
                    referrer_source = 'YouTube'
                elif 'reddit.com' in referrer_domain:
                    referrer_source = 'Reddit'
                else:
                    referrer_source = 'Referral'
            except:
                referrer_source = 'Referral'
        
        # Get page/section from custom data or URL
        page = post_data.get('page') or request.path
        action = post_data.get('action', 'pageview')
        
        # Get screen dimensions if available
        screen_width = post_data.get('screen_width')
        screen_height = post_data.get('screen_height')
        
        # Get session info
        session_id = post_data.get('session_id')
        
        # Create enriched visit document
        now = datetime.datetime.utcnow()
        
        new_visit = {
            # Basic request data
            **post_data,
            
            # Analytics metadata
            'analytics': {
                'session_id': session_id,
                'page': page,
                'action': action,
                'timestamp': now.isoformat(),
                'date': now.strftime("%Y-%m-%d"),
                'time': now.strftime("%H:%M:%S"),
                'day_of_week': now.strftime("%A"),
                'hour': now.hour,
                'month': now.strftime("%B"),
                'year': now.year,
            },
            
            # Visitor information
            'visitor': {
                'ip_address': ip_address,
                'device': {
                    'type': device_type,
                    'browser': browser,
                    'operating_system': os,
                    'user_agent': user_agent[:200] if user_agent else None,  # Truncate if too long
                    'screen_width': screen_width,
                    'screen_height': screen_height,
                },
                'language': headers.get('Accept-Language', '').split(',')[0] if headers.get('Accept-Language') else None,
            },
            
            # Traffic source
            'traffic_source': {
                'referrer': referrer,
                'referrer_domain': referrer_domain,
                'source': referrer_source,
                'utm_source': request.args.get('utm_source'),
                'utm_medium': request.args.get('utm_medium'),
                'utm_campaign': request.args.get('utm_campaign'),
                'utm_content': request.args.get('utm_content'),
                'utm_term': request.args.get('utm_term'),
            },
            
            # Engagement metrics (you can update these later)
            'engagement': {
                'time_on_page': post_data.get('time_on_page'),
                'scroll_depth': post_data.get('scroll_depth'),
                'clicks': post_data.get('clicks', 0),
                'is_bounce': True,  # Default to bounce, update if subsequent actions
                'first_visit': True,  # You'd track this via cookies/sessions
            },
            
            # Request metadata
            'request_metadata': {
                'method': request.method,
                'url': request.url,
                'path': request.path,
                'query_params': dict(request.args),
                'content_type': request.content_type,
                'content_length': request.content_length,
                'is_secure': request.is_secure,
                'headers_summary': {
                    'user_agent': bool(user_agent),
                    'accept_encoding': headers.get('Accept-Encoding'),
                    'accept_language': headers.get('Accept-Language'),
                    'connection': headers.get('Connection'),
                    'cache_control': headers.get('Cache-Control'),
                }
            },
            
            # System timestamps
            'timestamp': now,
            'server_timestamp': now.isoformat(),
        }
        
        # Insert into MongoDB collection
        result = visits_collection.insert_one(new_visit)
        visit_id = str(result.inserted_id)
        
        # Return success response with minimal data
        return jsonify({
            'success': True,
            'message': 'Visit recorded successfully',
            'visit_id': visit_id,
            'timestamp': now.isoformat()
        }), 201
        
    except Exception as e:
        # Log the error but don't expose details to client
        print(f"Error recording visit: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to record visit'
        }), 500

@app.route('/visits/insights', methods=['GET'])
def get_visits_insights():
    try:
        # Get time filter from query parameters (optional)
        days = int(request.args.get('days', 7))
        
        # Calculate date threshold
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        
        # Build insights
        insights = {
            'summary': {},
            'traffic_sources': {},
            'devices': {},
            'pages': {},
            'engagement': {},
            'timeline': {}
        }
        
        # 1. BASIC SUMMARY METRICS
        total_visits = visits_collection.count_documents({})
        recent_visits = visits_collection.count_documents({'timestamp': {'$gte': cutoff_date}})
        
        unique_ips_pipeline = [
            {'$group': {'_id': '$visitor.ip_address'}},
            {'$count': 'unique_visitors'}
        ]
        unique_ips_result = list(visits_collection.aggregate(unique_ips_pipeline))
        unique_visitors = unique_ips_result[0]['unique_visitors'] if unique_ips_result else 0
        
        # Get bounce rate (single page visits)
        bounce_pipeline = [
            {'$match': {'engagement.is_bounce': True}},
            {'$count': 'bounces'}
        ]
        bounce_result = list(visits_collection.aggregate(bounce_pipeline))
        bounces = bounce_result[0]['bounces'] if bounce_result else 0
        bounce_rate = (bounces / total_visits * 100) if total_visits > 0 else 0
        
        insights['summary'] = {
            'total_visits': total_visits,
            'recent_visits': recent_visits,
            'unique_visitors': unique_visitors,
            'avg_visits_per_day': round(recent_visits / days, 2) if days > 0 else 0,
            'bounce_rate': round(bounce_rate, 2)
        }
        
        # 2. TRAFFIC SOURCES
        traffic_pipeline = [
            {'$group': {
                '_id': '$traffic_source.source',
                'count': {'$sum': 1},
                'avg_time': {'$avg': '$engagement.time_on_page'}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        
        traffic_results = list(visits_collection.aggregate(traffic_pipeline))
        insights['traffic_sources'] = {
            'by_source': [
                {'source': item['_id'], 'count': item['count'], 'avg_time': round(item['avg_time'] or 0, 2)}
                for item in traffic_results
            ],
            'top_referrers': list(visits_collection.find(
                {'traffic_source.referrer_domain': {'$ne': None}},
                {'traffic_source.referrer_domain': 1, '_id': 0}
            ).distinct('traffic_source.referrer_domain')[:10])
        }
        
        # 3. DEVICE & BROWSER INSIGHTS
        device_pipeline = [
            {'$group': {
                '_id': '$visitor.device.type',
                'count': {'$sum': 1},
                'percentage': {'$avg': 1}
            }},
            {'$sort': {'count': -1}}
        ]
        
        device_results = list(visits_collection.aggregate(device_pipeline))
        insights['devices'] = {
            'by_type': [
                {'device': item['_id'], 'count': item['count'], 'percentage': round(item['percentage'] * 100, 2)}
                for item in device_results
            ],
            'browsers': list(visits_collection.find(
                {'visitor.device.browser': {'$ne': None}},
                {'visitor.device.browser': 1, '_id': 0}
            ).distinct('visitor.device.browser')[:5]),
            'operating_systems': list(visits_collection.find(
                {'visitor.device.operating_system': {'$ne': None}},
                {'visitor.device.operating_system': 1, '_id': 0}
            ).distinct('visitor.device.operating_system')[:5])
        }
        
        # 4. MOST POPULAR PAGES
        pages_pipeline = [
            {'$group': {
                '_id': '$analytics.page',
                'count': {'$sum': 1},
                'avg_time': {'$avg': '$engagement.time_on_page'},
                'bounce_rate': {
                    '$avg': {'$cond': [{'$eq': ['$engagement.is_bounce', True]}, 1, 0]}
                }
            }},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        
        pages_results = list(visits_collection.aggregate(pages_pipeline))
        insights['pages'] = {
            'most_visited': [
                {
                    'page': item['_id'],
                    'visits': item['count'],
                    'avg_time_seconds': round(item['avg_time'] or 0, 2),
                    'bounce_rate_percent': round((item['bounce_rate'] or 0) * 100, 2)
                }
                for item in pages_results
            ]
        }
        
        # 5. ENGAGEMENT METRICS
        scroll_pipeline = [
            {'$match': {'engagement.scroll_depth': {'$exists': True}}},
            {'$group': {
                '_id': None,
                'avg_scroll_depth': {'$avg': '$engagement.scroll_depth'},
                'max_scroll_depth': {'$max': '$engagement.scroll_depth'},
                'scrolled_users': {'$sum': 1}
            }}
        ]
        
        scroll_result = list(visits_collection.aggregate(scroll_pipeline))
        scroll_data = scroll_result[0] if scroll_result else {}
        
        insights['engagement'] = {
            'avg_scroll_depth': round(scroll_data.get('avg_scroll_depth', 0), 2),
            'max_scroll_depth': scroll_data.get('max_scroll_depth', 0),
            'users_who_scrolled': scroll_data.get('scrolled_users', 0),
            'total_clicks': visits_collection.count_documents({'action': 'click'}),
            'total_downloads': visits_collection.count_documents({'action': 'download'}),
            'avg_time_on_page': round(visits_collection.aggregate([
                {'$match': {'engagement.time_on_page': {'$exists': True, '$ne': None}}},
                {'$group': {'_id': None, 'avg': {'$avg': '$engagement.time_on_page'}}}
            ]).next().get('avg', 0) if visits_collection.count_documents({'engagement.time_on_page': {'$exists': True}}) > 0 else 0, 2)
        }
        
        # 6. TIMELINE DATA (last 30 days)
        if days <= 30:  # Only return timeline for reasonable timeframes
            timeline_pipeline = [
                {'$match': {'timestamp': {'$gte': cutoff_date}}},
                {'$group': {
                    '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$timestamp'}},
                    'visits': {'$sum': 1},
                    'unique_visitors': {'$addToSet': '$visitor.ip_address'}
                }},
                {'$project': {
                    'date': '$_id',
                    'visits': 1,
                    'unique_visitors': {'$size': '$unique_visitors'}
                }},
                {'$sort': {'date': 1}}
            ]
            
            timeline_results = list(visits_collection.aggregate(timeline_pipeline))
            insights['timeline'] = {
                'daily_visits': timeline_results,
                'period': f'last_{days}_days'
            }
        
        # 7. PEAK HOURS
        hour_pipeline = [
            {'$group': {
                '_id': '$analytics.hour',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ]
        
        hour_results = list(visits_collection.aggregate(hour_pipeline))
        insights['peak_hours'] = [
            {'hour': f"{item['_id']}:00", 'visits': item['count']}
            for item in hour_results
        ]
        
        # 8. RECENT ACTIVITY
        recent_activity = list(visits_collection.find(
            {},
            {
                'analytics.timestamp': 1,
                'analytics.page': 1,
                'visitor.device.type': 1,
                'visitor.device.browser': 1,
                'traffic_source.source': 1,
                'action': 1
            }
        ).sort('timestamp', -1).limit(10))
        
        # Convert ObjectId to string for JSON serialization
        for activity in recent_activity:
            activity['_id'] = str(activity['_id'])
        
        insights['recent_activity'] = recent_activity
        
        return jsonify({
            'success': True,
            'insights': insights,
            'generated_at': datetime.datetime.utcnow().isoformat(),
            'time_period': f'Last {days} days',
            'total_records_analyzed': total_visits
        }), 200
        
    except Exception as e:
        print(f"Error generating insights: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate insights',
            'message': str(e)
        }), 500
        
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
        "created_at": datetime.datetime.now().strftime("%B %-d, %Y")
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
        token = jwt.encode({"username": username, "exp": datetime.datetime.now() + datetime.timedelta(hours=24)}, jwt_secret, algorithm="HS256")
        print(username, " Logged in")
        return jsonify({"message": "Login successful", "token": token}), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401
    

@app.route('/generate_code', methods=['POST'])
@token_required
def generate_code():
    new_code = {
        "_id": ObjectId(),
        "code": str(random.randint(100000, 999999)),  # Generate a random 6-byte code
        "created_at": datetime.datetime.now().strftime("%B %-d, %Y")
    }
    codes_collection.insert_one(new_code)
    return jsonify({"message": "Registration code generated", "code": new_code["code"]}), 201


# Public endpoints
@app.route('/posts', methods=['GET'])
def get_posts():
    posts = list(posts_collection.find({'published': "true"}, {'_id': 1, 'title': 1, 'author': 1, 'date': 1})) 
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
@app.route('/posts-all', methods=['GET'])
@token_required
def get_posts_all():
    posts = list(posts_collection.find({}, {'_id': 1, 'title': 1, 'author': 1, 'date': 1, 'published': 1, 'update': 1})) 
    for post in posts:
        post['_id'] = str(post['_id']) 
    return jsonify(posts)

@app.route('/posts', methods=['POST'])
@token_required
def create_post():
    post_data = request.json

    new_post = {
        "_id": ObjectId(),
        "title": post_data.get("title"),
        "content": post_data.get("content"),
        "date": datetime.datetime.now().strftime("%B %-d, %Y"),
        "updated": "",
        "published": "true",
        "author": post_data.get("author")
    }

    posts_collection.insert_one(new_post)
    new_post["_id"] = str(new_post["_id"])
    
    return jsonify({"message": "Post created successfully", "post": new_post}), 201

@app.route('/posts/<string:id>/unpublish', methods=['PUT'])
@token_required
def unpublish_post(id):
    post_id = ObjectId(id)
    post = posts_collection.find_one({'_id': post_id}, {'_id': 1, 'title': 1, 'content': 1, 'author': 1, 'date': 1})
    
    if not post:
        return jsonify({"message": "Post not found"}), 404

    updated_post = {
        "published": "false"
    }

    result = posts_collection.update_one({"_id": post_id}, {"$set": updated_post})

    if result.matched_count == 0:
        return jsonify({"message": "No post unpublished, it may not exist"}), 404

    updated_post['_id'] = str(post_id)
    return jsonify({"message": "Post unpublished successfully", "post": updated_post}), 200

@app.route('/posts/<string:id>/publish', methods=['PUT'])
@token_required
def publish_post(id):
    post_id = ObjectId(id)
    post = posts_collection.find_one({'_id': post_id}, {'_id': 1, 'title': 1, 'content': 1, 'author': 1, 'date': 1})
    
    if not post:
        return jsonify({"message": "Post not found"}), 404

    updated_post = {
        "published": "true"
    }

    result = posts_collection.update_one({"_id": post_id}, {"$set": updated_post})

    if result.matched_count == 0:
        return jsonify({"message": "No post published, it may not exist"}), 404

    updated_post['_id'] = str(post_id)
    return jsonify({"message": "Post published successfully", "post": updated_post}), 200

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
        "updated": datetime.datetime.now().strftime("%B %-d, %Y")
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