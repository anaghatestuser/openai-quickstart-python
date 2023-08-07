# config.py
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()         # Initialize SQLAlchemy instance here
login = LoginManager()    # Initialize the LoginManager instance here


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
