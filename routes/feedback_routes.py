from flask import request, redirect, url_for
from flask_login import login_required

def init_app(app):

    @app.route('/submit_feedback', methods=['POST'])
    @login_required
    def submit_feedback():
        rating = request.form['rating']
        feedback = request.form['feedback']
        with open('feedback.txt', 'a') as file:
            file.write(f"Rating: {rating}\nFeedback: {feedback}\n\n")
        return redirect(url_for('home', feedback_message='Thank you for your feedback!'))
