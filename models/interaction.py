from datetime import datetime
from config import db

class Interaction(db.Model):
    """Model to store user interactions data."""
    
    id = db.Column(db.Integer, primary_key=True)
    statement = db.Column(db.Text, nullable=False)
    supportive_answer = db.Column(db.Text, nullable=False)
    opposing_answer = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Point to 'user.id' and remove the 'nullable' (it will be inferred from the ForeignKey)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))

    def __repr__(self):
        return f'<Interaction {self.id}>'
