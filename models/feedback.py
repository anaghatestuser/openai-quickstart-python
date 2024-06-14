from datetime import datetime
from config import db

class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Assuming user is required for feedback
    feedback_text = db.Column(db.String(1000))  # Adjust the max length as needed
    rating = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # relationship to User
    user = db.relationship("User", backref="feedback")
