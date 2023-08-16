from flask import request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models.feedback import Feedback
from config import db

def init_app(app):

    @app.route('/submit_feedback', methods=['POST'])
    @login_required
    def submit_feedback():
        rating = request.form.get('rating', type=int)
        feedback_text = request.form.get('feedback')

        # Validate input
        if not (1 <= rating <= 5):
            flash('Invalid rating provided.', 'error')
            return redirect(url_for('home'))

        if not feedback_text:
            flash('Feedback text cannot be empty.', 'error')
            return redirect(url_for('home'))

        # Create a new feedback object
        feedback = Feedback(
            rating=rating,
            feedback_text=feedback_text,
            user_id=current_user.id  # assuming Feedback model has a user_id column
        )

        # Add feedback to the database
        db.session.add(feedback)
        db.session.commit()

        # Logging the feedback submission
        current_app.logger.info(f"Feedback received from user {current_user.id} with rating {rating} and feedback text: '{feedback_text}'.")

        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('home'))
