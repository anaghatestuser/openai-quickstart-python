import csv
import logging
import random
import os
from datetime import datetime, timedelta

from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import current_user
from models.user import User
from config import db
from utils.logging_config import log_activity



def load_examples_from_csv(app, filename):
    with app.app_context():
        try:
            examples = []
            with current_app.open_resource(filename) as csvfile:
                content = csvfile.read().decode('utf-8')
                reader = csv.reader(content.splitlines())
                next(reader, None)  # skip the headers
                for row in reader:
                    examples.append((row[0], row[1], row[2]))
            logger.info("Loaded %d examples from %s", len(examples), filename)
            return examples
        except Exception as e:
            logger.error("Failed to load examples from %s: %s", filename, e)
            return []


def init_app(app):
    examples = load_examples_from_csv(app, 'csv/questions.csv')

    @app.route('/', methods=['GET'])
    def home():
        feedback_message = request.args.get('feedback_message', default=None, type=str)
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        statement, supportive_answer, opposing_answer = random.choice(examples)
        return render_template(
            'interaction/form.html', 
            feedback_message=feedback_message, 
            statement=statement, 
            supportive_answer=supportive_answer, 
            opposing_answer=opposing_answer
        )
