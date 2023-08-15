from flask import render_template, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from flask_mail import Message
from datetime import datetime
from models.user import User
from config import db, mail

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
        return render_template('users.html', users=users)
    
    @app.route('/make_admin/<username>')
    @login_required
    def make_admin(username):
        if not current_user.is_admin:
            abort(403)  # Only admin can make another user an admin
        user = User.query.filter_by(username=username).first()
        if not user:
            return "User not found"
        user.is_admin = True
        db.session.commit()
        return f"{username} is now an admin"

    @app.route('/users_unapproved')
    @login_required
    def users_unapproved():
        if not current_user.is_admin:
            abort(403)
        unapproved_users = User.query.filter_by(is_approved=False).all()
        return render_template('users_unapproved.html', users=unapproved_users)
    
    @app.route('/user_profile')
    @login_required
    def user_profile():
        if not current_user.is_approved:
            abort(403)  # Forbidden access for unapproved users
        # Additional logic to render a user profile or another action
        return render_template('user_profile.html', user=current_user, now=datetime.utcnow())


    @app.route('/approve_user/<int:user_id>')
    @login_required
    def approve_user(user_id):
        if not current_user.is_admin:
            abort(403)
        user = User.query.get(user_id)
        if not user:
            return "User not found"
        user.is_approved = True
        db.session.commit()
        flash(f"User {user.username} has been approved.")
        return redirect(url_for('users_unapproved'))
    
    @app.route('/bootstrap_admin')
    def bootstrap_admin():
        admin_username = 'Ulysses'  # Replace with your admin's username
        user = User.query.filter_by(username=admin_username).first()
        if user:
            user.is_approved = True
            db.session.commit()
            return f"{admin_username} is now approved"
        return "Admin user not found"

