from datetime import datetime
from config import db  # Adjusted the import statement

class Interaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    supportive_answer = db.Column(db.Text, nullable=False)
    opposing_answer = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Track when interaction took place
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link to the User model

    def __repr__(self):
        return '<Interaction %r>' % self.id
