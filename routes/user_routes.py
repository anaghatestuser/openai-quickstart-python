from flask import render_template, abort, flash, redirect, url_for, request
from flask_login import login_required, current_user, login_user, logout_user
from utils.logging_config import log_activity
from flask_mail import Message
from datetime import datetime, timedelta
from models.user import User
from config import db, mail
import logging

logger = logging.getLogger(__name__)

def init_app(app):

    @app.route('/test_mail')
    def test_mail():
        try:
            msg = Message('Hello from Flask-Mail', 
                          sender='ulysses@kissielts.com',
                          recipients=['ulysses@kissielts.com'])  # Replace with your email or another testing email
            msg.body = 'This is a test email sent from the Flask-Mail setup.'
            mail.send(msg)
            return "Email sent!"
        except Exception as e:
            return str(e)

    @app.route('/users')
    @login_required
    def get_users():
        if not current_user.is_admin:
            abort(403)  # abort with Forbidden status if the user is not admin
        users = User.query.all()
        return render_template('admin/users.html', users=users)
    
    @app.route('/make_admin/<username>')
    @login_required
    def make_admin(username):
        if not current_user.is_admin:
            logger.warning(f"Unauthorized access attempt to make {username} an admin")
            abort(403)  # Only admin can make another user an admin
        user = User.query.filter_by(username=username).first()
        if not user:
            logger.error(f"User {username} not found for admin creation")
            return "User not found"
        user.is_admin = True
        db.session.commit()
        logger.info(f"{username} is now an admin")
        return f"{username} is now an admin"
    
    @app.route('/user_profile')
    @login_required
    def user_profile():
        if not current_user.is_approved:
            abort(403)  # Forbidden access for unapproved users
        # Additional logic to render a user profile or another action
        return render_template('user/user_profile.html', user=current_user, now=datetime.utcnow())
    
    @app.route('/bootstrap_admin')
    def bootstrap_admin():
        admin_username = 'Ulysses'  # Replace with your admin's username
        user = User.query.filter_by(username=admin_username).first()
        if user:
            user.is_approved = True
            db.session.commit()
            return f"{admin_username} is now approved"
        return "Admin user not found"

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            if not username or not password:
                flash('Please enter both username and password.')
                return redirect(url_for('login'))

            user = User.query.filter_by(username=username).first()

            # Capturing IP address and user agent
            ip_address = request.remote_addr
            user_agent = request.user_agent.string

            if user is None or not user.check_password(password):
                logger.warning('Failed login attempt for username: %s', username)

                # Log the failed login attempt
                log_activity(None, "Attempted login", f"Failed login attempt for username: {username}", ip_address=ip_address, user_agent=user_agent)

                flash('Invalid username or password')
                return redirect(url_for('login'))

            # Setting login time
            user.login_time = datetime.utcnow()
            db.session.commit()

            if user.token_expiry_date and datetime.utcnow() > user.token_expiry_date:
                user.tokens = 0
                db.session.commit()
                flash('Your tokens have expired and have been reset to 0.', 'warning')

            if not user.is_approved:
                flash('Your account is awaiting approval by the admin.', 'warning')
                return redirect(url_for('login'))

            login_user(user)
            logger.info('User %s logged in successfully.', user.username)
            log_activity(user.id, "User Login", f"User {user.username} logged in.", ip_address=ip_address, user_agent=user_agent)
            return redirect(url_for('home'))

        return render_template('user/login.html')

    @app.route('/logout')
    @login_required
    def logout():
        # Check if login_time exists
        if current_user.login_time:
            duration = datetime.utcnow() - current_user.login_time
        else:
            duration = None

        ip_address = request.remote_addr
        user_agent = request.user_agent.string
            
        logger.info('User %s logged out.', current_user.username)
        log_activity(current_user.id, "User Logout", f"User {current_user.username} logged out.", duration=duration, ip_address=ip_address, user_agent=user_agent)
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
                return render_template('user/login.html', feedback_message='Username or email already exists. Please try a different one.')

            user = User(username=username, email=email, tokens=200)
            user.set_password(password)
            user.token_expiry_date = datetime.utcnow() + timedelta(days=60)
    
            db.session.add(user)
            db.session.commit()
            logger.info('User %s registered successfully.', user.username)
            log_activity(user.id, "User Registration", f"User {user.username} registered.")

            msg = Message('New User Registration', 
                  sender='ulysses@kissielts.com',
                  recipients=['ulysses@kissielts.com'])
            msg.body = f'New user {username} has registered and awaits approval.'
            try:
                mail.send(msg)
            except Exception as e:
                logger.error(f"Error sending mail: {e}")

            flash('Thank you for registering! Your account is awaiting approval by the admin.')
            return redirect(url_for('login'))

        return render_template('user/register.html')
