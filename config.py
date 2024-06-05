import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
from flask_mail import Mail
import logging
import sys

mail = Mail()

load_dotenv()

db = SQLAlchemy()
login = LoginManager()

SECRET_KEY = os.getenv('SECRET_KEY')
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
MAIL_SERVER = os.getenv('MAIL_SERVER')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'

MAIL_SENDER = 'ulysses@kissielts.com'
MAIL_SUBJECT = 'Account Approved - K.I.S.S. IELTS'
MAIL_BODY = ("Congratulations! Your K.I.S.S. IELTS A.I. account has been approved. "
             "You can now access our platform at {url}. "
             "Thank you for joining us!")

def configure_logging(app):
    # Configure logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    app.logger.setLevel(logging.DEBUG)
