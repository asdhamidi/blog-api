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
        days_param = request.args.get('days', '7')
        try:
            days = int(days_param)
        except ValueError:
            days = 7
        
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
        
        # Helper function to safely round
        def safe_round(value, decimals=2):
            if value is None:
                return 0
            try:
                return round(float(value), decimals)
            except (TypeError, ValueError):
                return 0
        
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
            'avg_visits_per_day': safe_round(recent_visits / days if days > 0 else 0),
            'bounce_rate': safe_round(bounce_rate)
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
                {
                    'source': item['_id'] or 'Unknown',
                    'count': item['count'],
                    'avg_time': safe_round(item['avg_time'])
                }
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
                {
                    'device': item['_id'] or 'Unknown',
                    'count': item['count'],
                    'percentage': safe_round((item.get('percentage') or 0) * 100)
                }
                for item in device_results
            ],
            'browsers': list(visits_collection.find(
                {'visitor.device.browser': {'$ne': None, '$ne': ''}},
                {'visitor.device.browser': 1, '_id': 0}
            ).distinct('visitor.device.browser')[:5]),
            'operating_systems': list(visits_collection.find(
                {'visitor.device.operating_system': {'$ne': None, '$ne': ''}},
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
                    'page': item['_id'] or '/',
                    'visits': item['count'],
                    'avg_time_seconds': safe_round(item['avg_time']),
                    'bounce_rate_percent': safe_round((item.get('bounce_rate') or 0) * 100)
                }
                for item in pages_results
            ]
        }
        
        # 5. ENGAGEMENT METRICS
        scroll_pipeline = [
            {'$match': {'engagement.scroll_depth': {'$exists': True, '$ne': None}}},
            {'$group': {
                '_id': None,
                'avg_scroll_depth': {'$avg': '$engagement.scroll_depth'},
                'max_scroll_depth': {'$max': '$engagement.scroll_depth'},
                'scrolled_users': {'$sum': 1}
            }}
        ]
        
        scroll_result = list(visits_collection.aggregate(scroll_pipeline))
        
        if scroll_result:
            scroll_data = scroll_result[0]
            avg_scroll = scroll_data.get('avg_scroll_depth')
            max_scroll = scroll_data.get('max_scroll_depth')
            scrolled_users = scroll_data.get('scrolled_users', 0)
        else:
            avg_scroll = 0
            max_scroll = 0
            scrolled_users = 0
        
        # Get average time on page safely
        time_pipeline = [
            {'$match': {'engagement.time_on_page': {'$exists': True, '$ne': None}}},
            {'$group': {'_id': None, 'avg': {'$avg': '$engagement.time_on_page'}}}
        ]
        
        time_result = list(visits_collection.aggregate(time_pipeline))
        avg_time = time_result[0]['avg'] if time_result else 0
        
        insights['engagement'] = {
            'avg_scroll_depth': safe_round(avg_scroll),
            'max_scroll_depth': safe_round(max_scroll, 0),  # No decimals for max
            'users_who_scrolled': scrolled_users,
            'total_clicks': visits_collection.count_documents({'action': 'click'}),
            'total_downloads': visits_collection.count_documents({'action': 'download'}),
            'avg_time_on_page': safe_round(avg_time)
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
        else:
            insights['timeline'] = {
                'daily_visits': [],
                'period': f'last_{days}_days',
                'note': 'Timeline data not available for periods longer than 30 days'
            }
        
        # 7. PEAK HOURS
        hour_pipeline = [
            {'$match': {'analytics.hour': {'$ne': None}}},
            {'$group': {
                '_id': '$analytics.hour',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ]
        
        hour_results = list(visits_collection.aggregate(hour_pipeline))
        insights['peak_hours'] = [
            {
                'hour': f"{int(item['_id'])}:00" if item['_id'] is not None else "Unknown",
                'visits': item['count']
            }
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
                'action': 1,
                'timestamp': 1
            }
        ).sort('timestamp', -1).limit(10))
        
        # Convert ObjectId to string for JSON serialization
        for activity in recent_activity:
            activity['_id'] = str(activity['_id'])
            # Ensure all fields exist
            activity.setdefault('analytics', {})
            activity.setdefault('visitor', {}).setdefault('device', {})
            activity.setdefault('traffic_source', {})
        
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
        import traceback
        traceback.print_exc()
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
        return jsonify({"m    print("Could not create indexes on visits collection:", e)


# Home route.
@app.route('/')
def home():
    return """
    Welcome to my Blog API!

    For full documentation and usage details, please visit:
    https://github.com/asdhamidi/blog-api/blob/main/README.md

    Happy trails!
    """


# --- Helpers for enhanced visit collection ---
MAX_UA_LEN = 512
MAX_REFERRER_LEN = 256
MAX_FIELD_LEN = 1024
IPINFO_TOKEN = os.getenv('IPINFO_TOKEN')


def _sanitize_keys(d):
    """Remove keys with dots or starting with $ (MongoDB operators) and truncate long strings."""
    safe = {}
    if not d:
        return safe
    for k, v in d.items():
        if not isinstance(k, str):
            continue
        if '.' in k or k.startswith('$'):
            continue
        if isinstance(v, str) and len(v) > MAX_FIELD_LEN:
            safe[k] = v[:MAX_FIELD_LEN]
        else:
            safe[k] = v
    return safe


def _get_client_ip(headers):
    # Respect common proxy headers; take first IP in X-Forwarded-For
    xff = headers.get('X-Forwarded-For') or headers.get('x-forwarded-for')
    if xff:
        return xff.split(',')[0].strip()
    xrip = headers.get('X-Real-IP') or headers.get('x-real-ip')
    if xrip:
        return xrip.strip()
    return request.remote_addr


def _hash_ip(ip, salt=None):
    if not ip:
        return None
    h = hashlib.sha256()
    if salt:
        h.update(salt.encode('utf-8'))
    h.update(ip.encode('utf-8'))
    return h.hexdigest()


def _geo_lookup(ip):
    try:
        if not ip:
            return None
        if GEOIP_READER:
            r = GEOIP_READER.city(ip)
            return {
                'country': r.country.name,
                'country_iso': r.country.iso_code,
                'region': r.subdivisions.most_specific.name,
                'city': r.city.name,
                'latitude': r.location.latitude,
                'longitude': r.location.longitude,
                'timezone': r.location.time_zone,
                'postal': r.postal.code,
            }
        elif IPINFO_TOKEN and requests:
            resp = requests.get(f'https://ipinfo.io/{ip}/json?token={IPINFO_TOKEN}', timeout=2)
            if resp.status_code == 200:
                j = resp.json()
                loc = j.get('loc', '')
                lat, lon = (loc.split(',') + [None, None])[:2]
                return {
                    'country': j.get('country'),
                    'region': j.get('region'),
                    'city': j.get('city'),
                    'latitude': float(lat) if lat else None,
                    'longitude': float(lon) if lon else None,
                    'timezone': j.get('timezone'),
                    'postal': j.get('postal'),
                    'org': j.get('org')
                }
    except Exception:
        pass
    return None


def _insert_visit_async(doc):
    def _worker(d):
        try:
            visits_collection.insert_one(d)
        except Exception as e:
            print("visit insert failed:", e)
    Thread(target=_worker, args=(doc,), daemon=True).start()


@app.route('/visit', methods=['POST', 'GET'])
def add_visit():
    """Enhanced visit endpoint: prefers POST JSON but accepts GET query params for backward compatibility.
    Extracts client hints, performance metrics, geo info (optional), UA-parsed details, and stores a privacy-aware doc.
    """
    try:
        body = request.get_json(silent=True) or {}
        if not body:
            body = {k: v for k, v in request.args.items()}
        body = _sanitize_keys(body)

        headers = {k: v for k, v in request.headers.items()}
        ip = _get_client_ip(request.headers)
        hashed_ip = _hash_ip(ip, salt=os.getenv("IP_HASH_SALT", ""))

        ua_string = headers.get('User-Agent', '') or ''
        ua_string_trunc = ua_string[:MAX_UA_LEN]
        ua = parse_ua(ua_string) if ua_string else None

        ua_data = {
            'user_agent': ua_string_trunc,
            'browser_family': ua.browser.family if ua else None,
            'browser_version': '.'.join([p for p in ua.browser.version if p]) if ua and ua.browser.version else None,
            'os_family': ua.os.family if ua else None,
            'os_version': '.'.join([p for p in ua.os.version if p]) if ua and ua.os.version else None,
            'device_family': ua.device.family if ua else None,
            'is_mobile': ua.is_mobile if ua else False,
            'is_tablet': ua.is_tablet if ua else False,
            'is_pc': ua.is_pc if ua else False,
            'is_bot': ua.is_bot if ua else False,
        }

        client_hints = {
            'sec_ch_ua': headers.get('Sec-CH-UA'),
            'sec_ch_ua_mobile': headers.get('Sec-CH-UA-Mobile'),
            'sec_ch_ua_platform': headers.get('Sec-CH-UA-Platform'),
            'dpr': headers.get('DPR'),
            'viewport_width': headers.get('Viewport-Width') or body.get('viewport_width'),
            'width': headers.get('Width') or body.get('width'),
            'save_data': headers.get('Save-Data') or body.get('save_data'),
        }

        perf = {
            'page_load_time': body.get('page_load_time'),
            'dom_content_loaded': body.get('dom_content_loaded'),
            'first_paint': body.get('first_paint'),
            'first_contentful_paint': body.get('first_contentful_paint'),
            'largest_contentful_paint': body.get('largest_contentful_paint'),
            'cumulative_layout_shift': body.get('cumulative_layout_shift'),
            'total_blocking_time': body.get('total_blocking_time'),
        }

        utm = {
            'utm_source': request.args.get('utm_source') or body.get('utm_source'),
            'utm_medium': request.args.get('utm_medium') or body.get('utm_medium'),
            'utm_campaign': request.args.get('utm_campaign') or body.get('utm_campaign'),
            'utm_term': request.args.get('utm_term') or body.get('utm_term'),
            'utm_content': request.args.get('utm_content') or body.get('utm_content'),
        }

        referrer = body.get('referrer') or request.referrer or headers.get('Referer') or None
        referrer = referrer[:MAX_REFERRER_LEN] if referrer else None
        ref_domain = urlparse(referrer).netloc if referrer else None

        event = {
            'type': body.get('event_type', body.get('action', 'pageview')),
            'element_id': body.get('element_id'),
            'element_selector': body.get('element_selector'),
            'link_url': body.get('link_url'),
            'link_text': body.get('link_text'),
        }

        def _to_int(v):
            try:
                return int(float(v))
            except Exception:
                return None

        screen_w = _to_int(body.get('screen_width'))
        screen_h = _to_int(body.get('screen_height'))
        clicks = _to_int(body.get('clicks')) or 0
        scroll_depth = None
        try:
            if body.get('scroll_depth') is not None:
                scroll_depth = float(body.get('scroll_depth'))
        except Exception:
            scroll_depth = None

        geo = _geo_lookup(ip)

        now = datetime.datetime.utcnow()

        visit_doc = {
            'schema_version': 2,
            'received_at': now,
            'client': {
                'ip_hash': hashed_ip,
                'ip_geo': geo,
                'language': (headers.get('Accept-Language') or '').split(',')[0] if headers.get('Accept-Language') else None,
                'referrer': referrer,
                'referrer_domain': ref_domain,
                'user_agent': ua_data,
                'client_hints': client_hints,
            },
            'analytics': {
                'session_id': body.get('session_id'),
                'visitor_id': body.get('visitor_id'),
                'page': body.get('page') or request.path,
                'url': request.url,
                'path': request.path,
                'event': event,
                'utm': utm,
                'timestamp': now,
                'date': now.strftime("%Y-%m-%d"),
                'hour': now.hour,
            },
            'engagement': {
                'screen_width': screen_w,
                'screen_height': screen_h,
                'clicks': clicks,
                'scroll_depth': scroll_depth,
                'is_bounce': bool(body.get('is_bounce', True)),
                'performance': perf,
            },
            'metadata': {
                'sample_rate': float(os.getenv('VISIT_SAMPLE_RATE', '1.0')),
                'sampled': False,
                'source_ip_raw_stored': False,
            }
        }

        sample_rate = float(os.getenv('VISIT_SAMPLE_RATE', '1.0'))
        if sample_rate < 1.0 and random.random() > sample_rate:
            visit_doc['metadata']['sampled'] = True
            return jsonify({'success': True, 'message': 'Visit sampled'}), 202

        _insert_visit_async(visit_doc)

        return jsonify({'success': True, 'message': 'Visit recorded', 'received_at': now.isoformat()}), 201

    except Exception as e:
        print("Error recording visit:", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to record visit'}), 500


@app.route('/visits/insights', methods=['GET'])
def get_visits_insights():
    """Build insights compatible with the enhanced visit schema.
    This aggregates by new field names (received_at, client.*, analytics.*, engagement.*)
    """
    try:
        days_param = request.args.get('days', '7')
        try:
            days = int(days_param)
        except ValueError:
            days = 7

        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)

        insights = {
            'summary': {},
            'traffic_sources': {},
            'devices': {},
            'pages': {},
            'engagement': {},
            'timeline': {}
        }

        def safe_round(value, decimals=2):
            if value is None:
                return 0
            try:
                return round(float(value), decimals)
            except (TypeError, ValueError):
                return 0

        # Basic summary
        total_visits = visits_collection.count_documents({})
        recent_visits = visits_collection.count_documents({'received_at': {'$gte': cutoff_date}})

        unique_ips_pipeline = [
            {'$group': {'_id': '$client.ip_hash'}},
            {'$count': 'unique_visitors'}
        ]
        unique_ips_result = list(visits_collection.aggregate(unique_ips_pipeline))
        unique_visitors = unique_ips_result[0]['unique_visitors'] if unique_ips_result else 0

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
            'avg_visits_per_day': safe_round(recent_visits / days if days > 0 else 0),
            'bounce_rate': safe_round(bounce_rate)
        }

        # Traffic sources (by referrer domain / UTM source)
        traffic_pipeline = [
            {'$group': {
                '_id': '$client.referrer_domain',
                'count': {'$sum': 1},
                'avg_time': {'$avg': '$engagement.performance.page_load_time'}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        traffic_results = list(visits_collection.aggregate(traffic_pipeline))
        insights['traffic_sources'] = {
            'by_referrer_domain': [
                {
                    'referrer_domain': item['_id'] or 'Direct',
                    'count': item['count'],
                    'avg_page_load_time': safe_round(item['avg_time'])
                }
                for item in traffic_results
            ],
            'by_utm_source': [
                {
                    'utm_source': group['_id'] or 'Unknown',
                    'count': group['count']
                }
                for group in list(visits_collection.aggregate([
                    {'$group': {'_id': '$analytics.utm.utm_source', 'count': {'$sum': 1}}},
                    {'$sort': {'count': -1}},
                    {'$limit': 10}
                ]))
            ]
        }

        # Device & browser insights
        device_pipeline = [
            {'$group': {
                '_id': '$client.user_agent.device_family',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}}
        ]
        device_results = list(visits_collection.aggregate(device_pipeline))
        insights['devices'] = {
            'by_device_family': [
                {'device': item['_id'] or 'Unknown', 'count': item['count']} for item in device_results
            ],
            'top_browsers': [
                {'browser': b, 'count': c} for b, c in list(visits_collection.aggregate([
                    {'$group': {'_id': '$client.user_agent.browser_family', 'count': {'$sum': 1}}},
                    {'$sort': {'count': -1}},
                    {'$limit': 5}
                ]))
            ]
        }

        # Most popular pages
        pages_pipeline = [
            {'$group': {
                '_id': '$analytics.page',
                'count': {'$sum': 1},
                'avg_load': {'$avg': '$engagement.performance.page_load_time'},
                'bounce_rate': {'$avg': {'$cond': [{'$eq': ['$engagement.is_bounce', True]}, 1, 0]}}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        pages_results = list(visits_collection.aggregate(pages_pipeline))
        insights['pages'] = {
            'most_visited': [
                {
                    'page': item['_id'] or '/',
                    'visits': item['count'],
                    'avg_page_load_time': safe_round(item.get('avg_load')),
                    'bounce_rate_percent': safe_round((item.get('bounce_rate') or 0) * 100)
                }
                for item in pages_results
            ]
        }

        # Engagement metrics
        scroll_pipeline = [
            {'$match': {'engagement.scroll_depth': {'$exists': True, '$ne': None}}},
            {'$group': {
                '_id': None,
                'avg_scroll_depth': {'$avg': '$engagement.scroll_depth'},
                'max_scroll_depth': {'$max': '$engagement.scroll_depth'},
                'scrolled_users': {'$sum': 1}
            }}
        ]
        scroll_result = list(visits_collection.aggregate(scroll_pipeline))
        if scroll_result:
            scroll_data = scroll_result[0]
            avg_scroll = scroll_data.get('avg_scroll_depth')
            max_scroll = scroll_data.get('max_scroll_depth')
            scrolled_users = scroll_data.get('scrolled_users', 0)
        else:
            avg_scroll = 0
            max_scroll = 0
            scrolled_users = 0

        time_pipeline = [
            {'$match': {'engagement.performance.page_load_time': {'$exists': True, '$ne': None}}},
            {'$group': {'_id': None, 'avg': {'$avg': '$engagement.performance.page_load_time'}}}
        ]
        time_result = list(visits_collection.aggregate(time_pipeline))
        avg_time = time_result[0]['avg'] if time_result else 0

        insights['engagement'] = {
            'avg_scroll_depth': safe_round(avg_scroll),
            'max_scroll_depth': safe_round(max_scroll, 0),
            'users_who_scrolled': scrolled_users,
            'total_clicks': visits_collection.count_documents({'engagement.clicks': {'$gt': 0}}),
            'total_downloads': visits_collection.count_documents({'analytics.event.type': 'download'}),
            'avg_page_load_time': safe_round(avg_time)
        }

        # Timeline (only if days <= 30)
        if days <= 30:
            timeline_pipeline = [
                {'$match': {'received_at': {'$gte': cutoff_date}}},
                {'$group': {
                    '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$received_at'}},
                    'visits': {'$sum': 1},
                    'unique_visitors': {'$addToSet': '$client.ip_hash'}
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
        else:
            insights['timeline'] = {
                'daily_visits': [],
                'period': f'last_{days}_days',
                'note': 'Timeline data not available for periods longer than 30 days'
            }

        # Peak hours
        hour_pipeline = [
            {'$match': {'analytics.hour': {'$ne': None}}},
            {'$group': {'_id': '$analytics.hour', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ]
        hour_results = list(visits_collection.aggregate(hour_pipeline))
        insights['peak_hours'] = [
            {'hour': f"{int(item['_id'])}:00" if item['_id'] is not None else 'Unknown', 'visits': item['count']} for item in hour_results
        ]

        # Recent activity
        recent_activity = list(visits_collection.find(
            {},
            {
                'analytics.timestamp': 1,
                'analytics.page': 1,
                'client.user_agent': 1,
                'client.referrer_domain': 1,
                'analytics.event': 1,
                'engagement': 1,
                'received_at': 1
            }
        ).sort('received_at', -1).limit(10))

        for activity in recent_activity:
            activity['_id'] = str(activity['_id'])
            activity.setdefault('analytics', {})
            activity.setdefault('client', {}).setdefault('user_agent', {})
            activity.setdefault('engagement', {})

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
        import traceback
        traceback.print_exc()
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
