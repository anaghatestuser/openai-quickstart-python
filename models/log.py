from datetime import datetime
from config import db

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # Time when the log was created
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # ForeignKey pointing to the User model
    action = db.Column(db.String(120))  # A short descriptor of the activity
    details = db.Column(db.String(500))  # Detailed information about the activity
    
    # Relationship with User model. 
    # This allows us to access the User of an ActivityLog with `activity_log_instance.user`
    # It also gives us a handy backref. A user instance will have an `activity_logs` attribute which returns all activity logs of that user.
    user = db.relationship('User', backref='activity_logs')
