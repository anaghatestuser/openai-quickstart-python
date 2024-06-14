import logging
from flask import request, redirect, url_for, flash, current_app, jsonify, render_template
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
        if rating is None or not (1 <= rating <= 5):
            return jsonify(status='error', message='Invalid rating provided.')

        if not feedback_text:
            return jsonify(status='error', message='Feedback text cannot be empty.')
            

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
        return jsonify(status="success", message="Thank you for your feedback!", redirect_url=url_for('home'))

    @app.route('/view_feedback', methods=['GET'])
    @login_required
    def view_feedback():
        feedback_list = Feedback.query.all()
        return render_template('admin/view_feedback.html', feedback_list=feedback_list)
