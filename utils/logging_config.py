from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from models.log import ActivityLog
from datetime import datetime
from config import db
import os
import sys
import logging


def log_activity(user_id, action, details, duration=None, ip_address=None, user_agent=None):
    log_entry = ActivityLog(
        timestamp=datetime.now(),
        user_id=user_id,
        action=action,
        details=details,
        duration=duration,  # This should be set
        ip_address=ip_address,     # Add IP address to the log entry if provided
        user_agent=user_agent      # Add User Agent to the log entry if provided
    )
    db.session.add(log_entry)
    db.session.commit()

    # This is where you can use your existing logger for application logs
    logger = logging.getLogger(__name__)
    logger.info(f"User {user_id} performed action: {action}. Details: {details}. IP: {ip_address}. User Agent: {user_agent}")
    

def configure_logging(app):
    log_dir = './logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Set up loggers and handlers
    file_handler_info = TimedRotatingFileHandler(os.path.join(log_dir, 'app_info.log'), when='D', interval=7, backupCount=4)
    file_handler_debug = RotatingFileHandler(os.path.join(log_dir, 'app_debug.log'), maxBytes=5000000, backupCount=1) # 5MB per file
    stream_handler = logging.StreamHandler(sys.stdout)

    file_handler_info.setLevel(logging.INFO)
    file_handler_debug.setLevel(logging.DEBUG)
    stream_handler.setLevel(logging.DEBUG)

    # Create a formatter and attach to handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler_info.setFormatter(formatter)
    file_handler_debug.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # Configure app.logger
    app.logger.addHandler(file_handler_info)
    app.logger.setLevel(logging.INFO)
    for logger in ["openai", "werkzeug"]:
        logging.getLogger(logger).setLevel(logging.WARNING)

    # Create a separate logger for debug messages
    logger_debug = logging.getLogger("app.debug")
    logger_debug.setLevel(logging.DEBUG)
    logger_debug.addHandler(file_handler_debug)
    logger_debug.addHandler(stream_handler)

    # Create a separate logger for this module
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(stream_handler)

    # Add stream handler to the logger
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger, logger_debug
