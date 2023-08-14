from flask import render_template, request
from flask_login import login_required, current_user
from models.user import User
from models.interaction import Interaction
from config import db as user_db
from utils.utilities import generate_reasons, deduct_tokens
import logging

logger = logging.getLogger(__name__)

def init_app(app):

    @app.route('/add_interaction/<int:user_id>/<statement>/<supportive_answer>/<opposing_answer>', methods=['GET', 'POST'])
    def add_interaction(user_id, statement, supportive_answer, opposing_answer):
        user = User.query.get(user_id)
        if user is None:
            return "User not found", 404
        interaction = Interaction(statement=statement, supportive_answer=supportive_answer, opposing_answer=opposing_answer, user_id=user.id)
        user_db.session.add(interaction)
        user_db.session.commit()
        return f"Added interaction for user: {user.username}"

    @app.route('/generate', methods=['POST'])
    @login_required
    def generate():
        user = current_user
        if user.tokens <= 0:
            return render_template('error.html', error_message='You have no tokens left.')
        statement = request.form['statement']
        logger.info(f"Generate request received. User: {user.username}, Statement: {statement}")
        try:
            reasons = generate_reasons(statement)
            logger.info(f"Generate reasons completed. User: {user.username}, Statement: {statement}")
        except Exception as e:
            logger.error(f"Failed to generate reasons. User: {user.username}, Statement: {statement}, Error: {str(e)}")
            return render_template('error.html', error_message='Failed to generate reasons.')

        deduct_tokens(user, 1)
        interaction = Interaction(statement=statement, 
                                  supportive_answer=reasons[0]['text'], 
                                  opposing_answer=reasons[1]['text'], 
                                  user_id=user.id)
        user.interactions.append(interaction)
        try:
            user_db.session.commit()
            logger.info("Interaction committed successfully.")
        except Exception as e:
            logger.error(f"Error committing interaction: {str(e)}")
        return render_template('results.html', reasons=reasons, statement=statement)

    @app.route('/generate_variation', methods=['POST'])
    @login_required
    def generate_variation():
        if current_user.tokens > 0:
            current_user.tokens -= 1
            user_db.session.commit()

            statement = request.form.get('statement')
            reasons = generate_reasons(statement)
            return render_template('results.html', reasons=reasons, statement=statement)
        else:
            error_message = "Sorry, you have no tokens left. Please purchase more to continue using the service."
            return render_template('results.html', error_message=error_message)
