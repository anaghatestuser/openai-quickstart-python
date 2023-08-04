from flask import render_template
from models.user import User

def init_app(app):

    @app.route('/users')
    def get_users():
        users = User.query.all()
        return render_template('users.html', users=users)
