import os
import openai
import traceback
from flask import Flask, render_template, current_app, request
from config import db, login
from models.user import User
from routes import main_routes, user_routes, interaction_routes, feedback_routes
from utils.logging_config import configure_logging
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash

def create_app():  # add an argument to control admin creation
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
    openai.api_key = os.getenv("OPENAI_API_KEY")
   
    # Define the create_admin flag
    create_admin = os.getenv("CREATE_ADMIN", "False").lower() == "true"

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

    db.init_app(app)  # Initialize db with app

    migrate = Migrate(app, db)

    login.init_app(app)  # Initialize login with app
    login.login_view = 'login'  # Updated from login_manager to login

    configure_logging(app)  # Call the function to configure logging

    with app.app_context():
        if create_admin:  # only create admin user if the flag is set
            print("Debug Admin Info:", os.getenv("ADMIN_USERNAME"), os.getenv("ADMIN_EMAIL"))
            create_admin_user()

    return app


def create_admin_user():
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_email = os.getenv("ADMIN_EMAIL")  # Add this line

    # Check if the admin user already exists
    admin_user = User.query.filter_by(username=admin_username).first()

    # If the admin user does not exist, create them
    if not admin_user:
        admin_user = User(username=admin_username, email=admin_email, password_hash=generate_password_hash(admin_password), is_admin=True)  # Update this line
        db.session.add(admin_user)
        db.session.commit()


app = create_app()
logger, logger_debug = configure_logging(app)

@login.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Initialize the routes
main_routes.init_app(app)
user_routes.init_app(app)
interaction_routes.init_app(app)
feedback_routes.init_app(app)

@app.errorhandler(500)
def internal_server_error(error):
    logger.error('Server Error: %s', (error))
    logger.error(traceback.format_exc())
    return "500 error", 500

@app.errorhandler(404)
def not_found_error(error):
    logger.warning('Page Not Found: %s, path: %s', error, request.path)
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
