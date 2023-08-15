from app import app, db  # Importing both the Flask app instance and the SQLAlchemy db instance.
from models.user import User
from datetime import datetime, timedelta


# Ensure your app context is initialized if necessary
# For instance, in Flask, you may need something like:
# from your_flask_app import app
# with app.app_context():

# Add 60 days for users without a set token_expiry_date
with app.app_context():
    # Update the token_expiry_date for users where it's None
    for user in User.query.filter_by(token_expiry_date=None).all():
        user.token_expiry_date = datetime.utcnow() + timedelta(days=60)

    # Set all users' tokens to 200
    for user in User.query.all():
        user.tokens = 200  # Assuming the token attribute is named 'tokens'

    db.session.commit()