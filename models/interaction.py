# models/interaction.py

from datetime import datetime
from config import db

class Interaction(db.Model):
    """Model to store user interactions data."""
    
    id = db.Column(db.Integer, primary_key=True)
    statement = db.Column(db.Text, nullable=False)
    supportive_answer = db.Column(db.Text, nullable=False)
    opposing_answer = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Interaction {self.id}>'
