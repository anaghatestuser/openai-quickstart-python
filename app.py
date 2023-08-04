import os
import traceback
from flask import Flask, render_template, current_app, request
from config import create_app, db, login
from models.user import User
from routes import main_routes, user_routes, interaction_routes, feedback_routes
from utils.logging_config import configure_logging

app = create_app()
logger, logger_debug = configure_logging(app)

@login.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

with app.app_context():
    # db.create_all()  # Uncomment this line to create tables & Comment this line again after the tables are created
    pass

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
    app.run(debug=False)
