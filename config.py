import os
import sys
import logging
from flask import Flask
from dotenv import load_dotenv
import openai
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

load_dotenv()

# Initialize SQLAlchemy instance here
db = SQLAlchemy()

login = LoginManager()  # Initialize the LoginManager instance here

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
    openai.api_key = os.getenv("OPENAI_API_KEY")

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

    db.init_app(app)  # Initialize db with app

    migrate = Migrate(app, db)

    login.init_app(app)  # Initialize login with app
    login.login_view = 'login'  # Updated from login_manager to login

    configure_logging(app)  # Call the function to configure logging

    return app

def configure_logging(app):
    # Configure logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Set level to DEBUG to ensure the log message gets handled
    stream_handler = logging.StreamHandler(sys.stdout)  # Creates a stream handler that logs to stdout
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # Creates a formatter
    stream_handler.setFormatter(formatter)  # Adds the formatter to the stream handler
    logger.addHandler(stream_handler)  # Adds the stream handler to the logger

    # Also set the level for the app logger
    app.logger.setLevel(logging.DEBUG)

app = create_app()
