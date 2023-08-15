from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_login import UserMixin
from config import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)  # Index added
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)  # Index added
    password_hash = db.Column(db.String(256), nullable=False)  # Increased hash length
    tokens = db.Column(db.Integer, default=200)  # Changed default from 1000 to 200
    is_admin = db.Column(db.Boolean, default=False)  # Indicates if the user has admin privileges
    interactions = db.relationship('Interaction', backref='user', lazy=True)
    is_approved = db.Column(db.Boolean, default=False)  # Indicates if the user account is approved
    token_expiry_date = db.Column(db.DateTime)  # Expiration date for the tokens, set this value appropriately

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)
