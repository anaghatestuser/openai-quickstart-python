import os
import traceback
import sys

from datetime import datetime
from dotenv import load_dotenv
import nltk
import openai
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import Flask, render_template, request, redirect, url_for, flash, current_app  # Import current_app here

from flask_sqlalchemy import SQLAlchemy  
from flask_migrate import Migrate
from sqlalchemy import Text
import string
import csv
import logging
from werkzeug.security import generate_password_hash, check_password_hash


nltk.download('punkt') # Add this line to download the 'punkt' resource

# Load variables from .env file into the environment
load_dotenv()

# Set the secret key for the Flask application
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")  # This should be the correct place to set the secret_key
openai.api_key = os.getenv("OPENAI_API_KEY")

# ensure logs directory exists
if not os.path.exists('logs'):
    os.makedirs('logs')


def configure_logging():
    # Configure logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Set level to DEBUG to ensure the log message gets handled
    stream_handler = logging.StreamHandler(sys.stdout)  # Creates a stream handler that logs to stdout
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s') # Creates a formatter
    stream_handler.setFormatter(formatter) # Adds the formatter to the stream handler
    logger.addHandler(stream_handler)  # Adds the stream handler to the logger
    
    # Also set the level for the app logger
    app.logger.setLevel(logging.DEBUG)
    
    return logger  # Return the logger object


# Add the following line to get the logger object
logger = configure_logging(app)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db = SQLAlchemy(app)  # Add this line to create a SQLAlchemy object
migrate = Migrate(app, db)  # Add this line to create a Migrate object

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# PostgreSQL database
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # Field for hashed password

    tokens = db.Column(db.Integer, default=1000)
    interactions = db.relationship('Interaction', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username


class Interaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    supportive_answer = db.Column(db.Text, nullable=False)
    opposing_answer = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Track when interaction took place
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link to the User model

    def __repr__(self):
        return '<Interaction %r>' % self.id

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    # db.create_all()  # Uncomment this line to create tables & Comment this line again after the tables are created
    pass

# SQLAlchemy routes
@app.route('/add_user/<username>/<email>')
def add_user(username, email):
    logger.info(f"Add user request received. Username: {username}, Email: {email}")
    user = User(username=username, email=email, tokens=1000)
    db.session.add(user)
    try:
        db.session.commit()
        logger.info(f"User added successfully. Username: {username}, Email: {email}")
    except Exception as e:
        logger.error(f"Failed to add user. Username: {username}, Email: {email}, Error: {str(e)}")
    return f"User: {username}, Email: {email} added."


@app.route('/users')
def get_users():
    users = User.query.all()
    return render_template('users.html', users=users)


@app.route('/add_interaction/<int:user_id>/<question>/<supportive_answer>/<opposing_answer>')
def add_interaction(user_id, question, supportive_answer, opposing_answer):
    user = User.query.get(user_id)
    if user is None:
        return "User not found", 404
    interaction = Interaction(question=question, supportive_answer=supportive_answer, opposing_answer=opposing_answer, user_id=user.id)
    db.session.add(interaction)
    db.session.commit()
    return f"Added interaction for user: {user.username}"


# Create a new route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()  # Remove 'email' from the query
        if user is None or not user.check_password(password):
            logger.warning('Failed login attempt for username: %s', username)
            flash('Invalid username or password')
            return redirect(url_for('login'))  # This will redirect to the login page

        login_user(user)
        logger.info('User %s logged in successfully.', user.username)
        return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    # Use current_app.logger instead of logger
    current_app.logger.info('User %s logged out.', current_user.username)
    logout_user()
    return redirect(url_for('login'))  # This will redirect to the login page

# Add the following route for registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Check if the username or email already exists in the database
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_user or existing_email:
            return render_template('login.html', feedback_message='Username or email already exists. Please try a different one.')

        # Create a new user and add them to the database
        user = User(username=username, email=email, tokens=1000)
        user.set_password(password)  # Hash and store the password
        db.session.add(user)
        db.session.commit()

        # Log in the user after successful registration
        login_user(user)

        # Redirect the user to the home page or any other page you want
        return redirect(url_for('home'))

    return render_template('register.html')


# Function to read CSV examples
def read_csv_examples(file_path):
    examples = []
    with open(file_path, 'r', encoding='utf-8-sig') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            question = row['Question']
            supportive_answer = row['Supportive Answer']
            opposing_answer = row['Opposing Answer']
            examples.append((question, supportive_answer, opposing_answer))
    return examples


csv_file_path = './csv/questions.csv'

print("Current working directory:", os.getcwd())  # Add this line

examples = read_csv_examples(csv_file_path)

def capitalize_first_letter(text):
    sentences = nltk.sent_tokenize(text)
    capitalized_sentences = []
    for sentence in sentences:
        # Capitalize the first letter of each sentence and make the rest of the sentence lowercase
        capitalized_sentence = sentence.strip().capitalize()
        capitalized_sentences.append(capitalized_sentence)
    return ' '.join(capitalized_sentences)

# Modify the existing extract_complete_answer function
def extract_complete_answer(text, max_words):
    words = text.split()
    if len(words) <= max_words:
        return ' '.join(words)
    else:
        extracted_words = words[:max_words]
        for i in range(max_words-1, -1, -1):
            if extracted_words[i][-1] in {'.', '?', '!'}:
                return capitalize_first_letter(' '.join(extracted_words[:i+1]))
        return capitalize_first_letter(' '.join(extracted_words))


def generate_reasons(question):
    supporting_prompt = f"Pretend you are an IELTS Band 9 Writing Task 2 examiner who is capable of writing a 120 words paragraph. ONLY discuss ONE reason to agree with a statement. The reason should be one of the following: creativity, critical-thinking, empathy, face-to-face communication skills, better memory of content, concentration, accountability, motivation, physical health, belonging, self-esteem, identity, lonely, feel connected, feel secure, efficient work, efficient study, efficient life, earn more money, happy, feel stressed, feel relaxed, good environment, sustainable development, less crimes, cultural identity, social cohesion, economic growth. Write this reason clearly in the first sentence, explain it specifically, logically, and sufficiently with a clear logical progression. Avoid using 'Although', 'but', 'However', and sophisticated words. \n\nFor the question: '{question}', provide a supporting reason."

    try:
        supporting_response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=supporting_prompt,
            max_tokens=200,
            n=1,
            stop=".\\n\\n",
            temperature=0.6
        ).choices[0].text.strip()

        # Use extract_complete_answer function to limit the length of the response
        supporting_response = extract_complete_answer(supporting_response, 100)
        supporting_response = capitalize_first_letter(supporting_response)

        logger.info(f"Supporting Response for question '{question}': {supporting_response}")
    except Exception as e:
        logger.error(f"Error generating supporting response for question '{question}': {str(e)}")
        supporting_response = "Error generating supporting response"

    opposing_prompt = f"Pretend you are an IELTS Band 9 Writing Task 2 examiner who is capable of writing a 120 words paragraph. ONLY discuss ONE reason to disagree with a statement. The reason should be one of the following: creativity, critical-thinking, empathy, face-to-face communication skills, better memory of content, concentration, accountability, motivation, physical health, belonging, self-esteem, identity, lonely, feel connected, feel secure, efficient work, efficient study, efficient life, earn more money, happy, feel stressed, feel relaxed, good environment, sustainable development, less crimes, cultural identity, social cohesion, economic growth. Write this reason clearly in the first sentence, explain it specifically, logically, and sufficiently with a clear logical progression. Avoid using 'Although', 'but', 'However', and sophisticated words. \n\nFor the question: '{question}', provide an opposing reason."

    try:
        opposing_response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=opposing_prompt,
            max_tokens=200,
            n=1,
            stop=".\\n\\n",
            temperature=0.6
        ).choices[0].text.strip()

        # Use extract_complete_answer function to limit the length of the response
        opposing_response = extract_complete_answer(opposing_response, 100)
        opposing_response = capitalize_first_letter(opposing_response)


        logger.info(f"Opposing Response for question '{question}': {opposing_response}")
    except Exception as e:
        logger.error(f"Error generating opposing response for question '{question}': {str(e)}")
        opposing_response = "Error generating opposing response"

    response = [
        {'title': 'Supporting reason:', 'text': supporting_response},
        {'title': 'Opposing reason:', 'text': opposing_response}
    ]

    return response


def lexicon_count(text, removepunct=False):
    if removepunct:
        # Remove punctuation from the text
        text = text.translate(str.maketrans('', '', string.punctuation))

    # Split the text into words and count them
    return len(text.split())

import random

@app.route('/', methods=['GET'])
def home():
    feedback_message = request.args.get('feedback_message', default=None, type=str)
    
    # Check if the user is logged in
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    random_example = random.choice(examples)
    question = random_example[0]
    supportive_answer = random_example[1]
    opposing_answer = random_example[2]
    return render_template('form.html', feedback_message=feedback_message, question=question, supportive_answer=supportive_answer, opposing_answer=opposing_answer)


@app.route('/generate', methods=['POST'])
@login_required
def generate():
    # Get the current user
    user = current_user

    # Check if the user has tokens left
    if user.tokens <= 0:
        return render_template('error.html', error_message='You have no tokens left.')

    # Get the question from the form
    question = request.form['question']
    logger.info(f"Generate request received. User: {user.username}, Question: {question}")

    # Generate the reasons
    try:
        reasons = generate_reasons(question)
        logger.info(f"Generate reasons completed. User: {user.username}, Question: {question}")
    except Exception as e:
        logger.error(f"Failed to generate reasons. User: {user.username}, Question: {question}, Error: {str(e)}")
        return render_template('error.html', error_message='Failed to generate reasons.')
    
    # Deduct a token from the user's account
    deduct_tokens(user, 1)  # use the new function here

    # Store the interaction in the database
    interaction = Interaction(question=question, 
                              supportive_answer=reasons[0]['text'], 
                              opposing_answer=reasons[1]['text'], 
                              user_id=user.id)
    db.session.add(interaction)
    try:
        db.session.commit()
        logger.info("Interaction committed successfully.") # Debug print
    except Exception as e:
        logger.error(f"Error committing interaction: {str(e)}")

    return render_template('results.html', reasons=reasons, question=question)

def deduct_tokens(user, tokens):
    logger.debug(f"Deducting {tokens} tokens from user {user.id}")
    user.tokens -= tokens
    try:
        db.session.commit()
        print("Token deduction committed successfully.") # Debug print
    except Exception as e:
        print("Error committing token deduction: ", e)

@app.route('/generate_variation', methods=['POST'])
@login_required
def generate_variation():
    # Deduct a token if the user has tokens
    if current_user.tokens > 0:
        current_user.tokens -= 1
        db.session.commit()
        
        question = request.form.get('question')
        reasons = generate_reasons(question) # Assuming generate_reasons() function handles generation of new reasons
        return render_template('results.html', reasons=reasons, question=question)
    else:
        # If the user has no tokens left, return an error message
        error_message = "Sorry, you have no tokens left. Please purchase more to continue using the service."
        return render_template('results.html', error_message=error_message)


@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    rating = request.form['rating']
    feedback = request.form['feedback']
    
    # Save the feedback to the file
    with open('feedback.txt', 'a') as file:
        file.write(f"Rating: {rating}\nFeedback: {feedback}\n\n")
    
    # Redirect back to the main page with a thank you message
    return render_template('form.html', feedback_message='Thank you for your feedback!')


@app.errorhandler(500)
def internal_server_error(error):
    app.logger.error('Server Error: %s', str(error))
    app.logger.error(traceback.format_exc())
    return "500 error", 500

if __name__ == '__main__':
    configure_logging()  # Invoke the configure_logging function before starting the server
    app.run(debug=False)