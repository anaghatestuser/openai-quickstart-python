from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from config import db

class User(UserMixin, db.Model):
    """User model representing application users."""
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    tokens = db.Column(db.Integer, default=100)
    is_admin = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    token_expiry_date = db.Column(db.DateTime)
    
    interactions = db.relationship('Interaction', backref='owner', lazy=True)
    
    login_time = db.Column(db.DateTime)  # Add this line for the login_time attribute

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self, expires_sec=1800):
        secret_key = current_app.config['SECRET_KEY']
        print(f"SECRET_KEY: {secret_key}")
        print(f"SECRET_KEY type: {type(secret_key)}")
        
        if isinstance(secret_key, str):
            secret_key = secret_key.encode('utf-8')
        
        print(f"Encoded SECRET_KEY: {secret_key}")
        print(f"Encoded SECRET_KEY type: {type(secret_key)}")
        
        s = Serializer(secret_key)
        print(f"Serializer initialized with secret_key: {secret_key}")
        
        # Generate token with the expiration time
        token = s.dumps({'user_id': self.id}, salt='password-reset-salt')
        print(f"Generated token: {token}")
        
        return token  # Removed .decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        secret_key = current_app.config['SECRET_KEY']
        if isinstance(secret_key, str):
            secret_key = secret_key.encode('utf-8')
        s = Serializer(secret_key)
        try:
            user_id = s.loads(token, salt='password-reset-salt')['user_id']
        except Exception as e:
            print(f"Error in verify_reset_token: {e}")
            return None
        return User.query.get(user_id)
