import logging
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.user import User
from models.interaction import Interaction
from config import db
from utils.utilities import generate_reasons, deduct_tokens

logger = logging.getLogger(__name__)

def init_app(app):

    @app.route('/form_page', methods=['GET'])
    @login_required
    def form_page():
        return render_template('interaction/form.html')

    @app.route('/add_interaction/<int:user_id>/<statement>/<supportive_answer>/<opposing_answer>', methods=['GET', 'POST'])
    def add_interaction(user_id, statement, supportive_answer, opposing_answer):
        user = User.query.get(user_id)
        if user is None:
            logger.error("User not found while trying to add interaction")
            return "User not found", 404

        interaction = Interaction(
            statement=statement,
            supportive_answer=supportive_answer,
            opposing_answer=opposing_answer,
            user_id=user.id
        )
        
        db.session.add(interaction)
        db.session.commit() 

        logger.info(f"Added interaction for user: {user.username}")
        return f"Added interaction for user: {user.username}"

    @app.route('/generate', methods=['POST'])
    @login_required
    def generate():
        user = current_user
        if user.tokens <= 0:
            flash('You have no tokens left.', 'error')
            return redirect(url_for('home'))

        statement = request.form['statement'].strip()
        if not statement:
            flash('Statement cannot be empty.', 'error')
            return redirect(url_for('home'))

        choice = request.form['choice']
        logger.info(f"Generate request received. User: {user.username}, Statement: {statement}")

        try:
            reasons = generate_reasons(statement, choice)
            if len(reasons) >= 2:
                supportive_answer = reasons[0]['text']
                opposing_answer = reasons[1]['text']
            else:
                logger.error(f"Expected 2 reasons but got {len(reasons)}. User: {user.username}, Statement: {statement}")
                flash('Failed to generate reasons. Please try again later.', 'error')
                return redirect(url_for('home'))

            deduct_tokens(user, 1)

            interaction = Interaction(
                statement=statement,
                supportive_answer=supportive_answer,
                opposing_answer=opposing_answer,
                user_id=user.id
            )

            user.interactions.append(interaction)
            db.session.commit()
            logger.info("Interaction committed successfully.")
            
        except Exception as e:
            logger.error(f"Failed to generate reasons. User: {user.username}, Statement: {statement}, Error: {str(e)}")
            flash('Failed to generate reasons. Please try again later.', 'error')
            return redirect(url_for('home'))

        return render_template('interaction/results.html', reasons=reasons, statement=statement)

    @app.route('/generate_variation', methods=['POST'])
    @login_required
    def generate_variation():
        if current_user.tokens <= 0:
            flash('Sorry, you have no tokens left. Please purchase more to continue using the service.', 'error')
            return redirect(url_for('home'))

        statement = request.form.get('statement').strip()
        choice = request.form.get('choice')  # Get the choice

        if not statement:
            flash('Statement cannot be empty.', 'error')
            return redirect(url_for('home'))

        reasons = generate_reasons(statement, choice)  # Pass the choice to generate_reasons
        return render_template('interaction/results.html', reasons=reasons, statement=statement)
