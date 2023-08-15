from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user, login_user, logout_user
from datetime import datetime, timedelta
from config import db as user_db, mail
from werkzeug.urls import url_parse
from flask_mail import Message
from models.user import User
import logging
import random
import csv
import os


logger = logging.getLogger(__name__)

def load_examples_from_csv(app, filename):
    with app.app_context():
        try:
            examples = []
            with current_app.open_resource(filename) as csvfile:
                content = csvfile.read().decode('utf-8')
                reader = csv.reader(content.splitlines())
                next(reader, None)  # skip the headers
                for row in reader:
                    examples.append((row[0], row[1], row[2]))
            logger.info("Loaded %d examples from %s", len(examples), filename)
            return examples
        except Exception as e:
            logger.error("Failed to load examples from %s: %s", filename, e)
            return []



def init_app(app):
    examples = load_examples_from_csv(app, 'csv/questions.csv')

    @app.route('/', methods=['GET'])
    def home():
        feedback_message = request.args.get('feedback_message', default=None, type=str)
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        random_example = random.choice(examples)
        statement = random_example[0]
        supportive_answer = random_example[1]
        opposing_answer = random_example[2]
        return render_template('form.html', feedback_message=feedback_message, statement=statement, supportive_answer=supportive_answer, opposing_answer=opposing_answer)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            if not username or not password:
                flash('Please enter both username and password.')
                return redirect(url_for('login'))

            user = User.query.filter_by(username=username).first()

            if user is None or not user.check_password(password):
                logger.warning('Failed login attempt for username: %s', username)
                flash('Invalid username or password')
                return redirect(url_for('login'))  
            
            if user is not None and user.check_password(password):
                # New logic to check if tokens have expired
                if user.token_expiry_date and datetime.utcnow() > user.token_expiry_date:
                    user.tokens = 0  # Set tokens to 0 if they're expired
                    user_db.session.commit()  # Save changes to the database
                    flash('Your tokens have expired and have been reset to 0.', 'warning')
            

            # Check if the user is approved
            if not user.is_approved:
                flash('Your account is awaiting approval by the admin.', 'warning')
                return redirect(url_for('login'))

            login_user(user)
            logger.info('User %s logged in successfully.', user.username)
            return redirect(url_for('home'))

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logger.info('User %s logged out.', current_user.username)
        logout_user()
        return redirect(url_for('login'))  

    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']

            if not username or not password or not email:
                flash('Please fill in all the fields.')
                return redirect(url_for('register'))

            existing_user = User.query.filter_by(username=username).first()
            existing_email = User.query.filter_by(email=email).first()

            if existing_user or existing_email:
                logger.warning('Attempt to register with already existing username or email: %s, %s', username, email)
                return render_template('login.html', feedback_message='Username or email already exists. Please try a different one.')

            # Create the user once and set all its attributes
            user = User(username=username, email=email, tokens=200)  # Tokens set to 200 here
            user.set_password(password)
            user.token_expiry_date = datetime.utcnow() + timedelta(days=60)  # Set the token expiry

            user_db.session.add(user)
            user_db.session.commit()
            logger.info('User %s registered successfully.', user.username)

            # After the user is saved to the database, send an email to the admin
            msg = Message('New User Registration', 
                  sender='ulysses@kissielts.com',
                  recipients=['ulysses@kissielts.com'])  # Adjust this to the admin's email
            msg.body = f'New user {username} has registered and awaits approval.'
            try:
                mail.send(msg)
            except Exception as e:
                print(f"Error sending mail: {e}")

            flash('Thank you for registering! Your account is awaiting approval by the admin.')
            return redirect(url_for('login'))

        return render_template('register.html')