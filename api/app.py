from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from auth import auth_bp
from posts import posts_bp
from codes import codes_bp
import os

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.config.from_pyfile('config.py')

app.register_blueprint(auth_bp)
app.register_blueprint(posts_bp)
app.register_blueprint(codes_bp)

@app.route("/")
def home():
    return """
    Welcome to my Blog API!

    For full documentation and usage details, please visit:
    https://github.com/asdhamidi/blog-api/blob/main/README.md

    Happy trails!
    """

if __name__ == '__main__':
    app.run(debug=True)
