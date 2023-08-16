from datetime import datetime
from config import db

class ActivityLog(db.Model):
    """Model representing activity logs for user actions."""
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    duration = db.Column(db.Interval)  # Duration for which the user was logged in
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(120))
    details = db.Column(db.String(500))
    user = db.relationship('User', backref='activity_logs')
    ip_address = db.Column(db.String(45))  # Enough space for IPv4 and IPv6 addresses
    user_agent = db.Column(db.String(500))  # Arbitrary length, adjust as necessary

