import os
import openai
import traceback
from flask import Flask, render_template, current_app, request
from config import db, login, mail
from models.user import User
from utils.logging_config import configure_logging
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    create_admin = os.getenv("CREATE_ADMIN", "False").lower() == "true"
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False') == 'False'

    db.init_app(app)

    migrate = Migrate(app, db)

    login.init_app(app)
    login.login_view = 'login'
    mail.init_app(app)

    configure_logging(app)  # Configure logging

    with app.app_context():
        if create_admin:
            create_admin_user()

    return app

def create_admin_user():
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_email = os.getenv("ADMIN_EMAIL")

    admin_user = User.query.filter_by(username=admin_username).first()

    if not admin_user:
        admin_user = User(username=admin_username, email=admin_email, password_hash=generate_password_hash(admin_password), is_admin=True)
        db.session.add(admin_user)
        db.session.commit()

app = create_app()
configure_logging(app)  # Configure loggers

@login.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

from routes import main_routes, user_routes, interaction_routes, feedback_routes, admin_routes

main_routes.init_app(app)
user_routes.init_app(app)
interaction_routes.init_app(app)
feedback_routes.init_app(app)
admin_routes.init_app(app)

@app.errorhandler(500)
def internal_server_error(error):
    logger.error('Server Error: %s', (error))
    logger.error(traceback.format_exc())
    return render_template('errors/500.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    logger.warning('Page Not Found: %s, path: %s', error, request.path)
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
    logger.warning('Forbidden Request: %s, path: %s', error, request.path)
    return render_template('errors/403.html'), 403

if __name__ == '__main__':
    app.run(debug=False)
