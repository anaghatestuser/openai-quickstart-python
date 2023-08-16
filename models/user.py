from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_login import UserMixin
from config import db

class User(UserMixin, db.Model):
    """User model representing application users."""
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    tokens = db.Column(db.Integer, default=200)
    is_admin = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    token_expiry_date = db.Column(db.DateTime)
    interactions = db.relationship('Interaction', backref='user', lazy=True)
    login_time = db.Column(db.DateTime)  # Add this line for the login_time attribute

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)
    
