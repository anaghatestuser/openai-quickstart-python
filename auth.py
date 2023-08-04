import os
import jwt
from models.user import User
from datetime import datetime, timedelta
from config import db, create_app, login  # Import db, create_app function, and login variable from config
from flask_login import LoginManager, login_user
from utils.logging_config import configure_logging  # Import the configure_logging function from utils

app = create_app()  # Get the app instance from create_app function
logger = configure_logging(app)  # Configure logging with the app instance

# Define the login manager for the app
login = LoginManager(app)
login.login_view = 'login'  # Updated from login_manager to login


def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    token = jwt.encode(payload, app.secret_key, algorithm='HS256')
    return token

def verify_token(token):
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def encode_jwt(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, app.secret_key, algorithm='HS256')

def decode_jwt(token):
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None  # Token has expired
    except jwt.InvalidTokenError:
        return None  # Invalid token

def authenticate(username, password):
    # Check user credentials, hash the password, and compare with the stored password hash in the database
    user = User.query.filter_by(username=username).first()
    if user:
        logger.debug(f"User found: {user.username}")
        if user.check_password(password):
            logger.debug("Password is correct. Authentication successful.")
            return user
        else:
            logger.debug("Incorrect password. Authentication failed.")
    else:
        logger.debug(f"User not found for username: {username}")

    return None

def get_token_from_request(request):
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer'):
        return auth_header.split()[1]
    return None
