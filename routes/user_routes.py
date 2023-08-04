from flask import render_template, abort
from models.user import User
from flask_login import login_required, current_user

def init_app(app):

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
