import os
import nltk
import string
from openai import OpenAI, OpenAIError  # Correct import

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import logging
import random
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app, url_for
from flask_mail import Message
from config import db, mail


# Configuration setup
ENGINE_NAME = os.environ.get('OPENAI_ENGINE_NAME', 'gpt-3.5-turbo-instruct')
is_on_render = os.environ.get('IS_ON_RENDER', 'False').lower() == 'true'
nltk_data_path = os.environ.get('NLTK_DATA_PATH', '/opt/render/project/src/nltk_data') if is_on_render else os.path.expanduser('~/nltk_data')
data_path = os.path.join(nltk_data_path, 'tokenizers/punkt')

# Download punkt tokenizer if not available
if not os.path.exists(data_path):
    nltk.download('punkt', download_dir=nltk_data_path)
nltk.data.path.append(nltk_data_path)

def capitalize_first_letter(text):
    """Capitalize the first letter of each sentence in the given text."""
    sentences = nltk.sent_tokenize(text)
    return ' '.join(sentence.capitalize() for sentence in sentences)

def extract_complete_answer(text, max_words):
    """Extract a complete answer from a text, ensuring the text does not exceed max_words."""
    words = text.split()
    if len(words) <= max_words:
        return ' '.join(words)

    extracted_words = words[:max_words]
    for i in range(max_words-1, -1, -1):
        if extracted_words[i][-1] in {'.', '?', '!'}:
            return capitalize_first_letter(' '.join(extracted_words[:i+1]))
    return capitalize_first_letter(' '.join(extracted_words[:max_words]))

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

REASONS_LIST = [
    "creativity", "critical thinking", "empathy", "face-to-face communication skills", "better memory of content", 
    "concentration", "accountability", "motivation", "physical health", "belonging", "self-esteem", "identity", "lonely", 
    "feeling connected", "feeling secure", "efficient work", "efficient study", "efficient life", "earning more money", 
    "happy", "feel stressed", "feel relaxed", "good environment", "sustainable development", "less crimes", "cultural identity", 
    "social cohesion", "economic growth", "competitive work environment", "schools too much focus on academic study", 
    "boring content", "interesting content", "gender stereotypes", "practical skills", "technology development", "media influence", 
    "urbanisation", "overuse natural resources", "government focus too much on economic growth"
]

def generate_supportive_prompt(statement, paragraph_number, reasons=None):
    """Generate a prompt for generating Supportive paragraphs for IELTS writing task."""

    seeding_reason = f"Anchor your exposition around the reason: '{random.choice(reasons)}'. This reason should directly and unequivocally resonate with the core statement." if reasons else ""

    base_prompt = (
        f"You're tasked with simulating an IELTS Band 9 Writing Task 2 response. {seeding_reason}"
        "To achieve this standard, compose a 150-word paragraph adhering to these guidelines:"
        "\n1. Directly address the given statement and avoid ambiguous interpretations. Stay true to the core topic throughout."
        "\n2. Focus on one main idea and develop it thoroughly. Explain its significance, implications, and how it ties back to the central theme."
        "\n3. Provide relevant examples and evidence to support your points."
        "\n4. Use a variety of sentence structures and maintain a formal tone."
        "\n5. Ensure the paragraph doesn't overlap with other arguments and offers a fresh perspective."
        "\n6. Conclude the paragraph effectively, reinforcing the main idea discussed."
        "\nAim for depth, precision, and utmost relevance. Stay on topic and ensure every point made is pertinent to the central theme."
    )

    return f"{base_prompt}\n\nIn paragraph {paragraph_number}, the statement reads: '{statement}'. Craft a paragraph that supports this contention, focusing on a single-threaded, detailed elucidation of the reason specified, ensuring it harmonizes seamlessly with the statement's main theme."

def generate_opposing_prompt(statement, paragraph_number, reasons=None):
    """Generate a prompt for generating Opposing paragraphs for IELTS writing task."""

    seeding_reason = f"Anchor your exposition around the reason: '{random.choice(reasons)}'. This reason should directly and unequivocally resonate with the core statement." if reasons else ""

    base_prompt = (
        f"You're tasked with simulating an IELTS Band 9 Writing Task 2 response. {seeding_reason}"
        "To achieve this standard, compose a 150-word paragraph adhering to these guidelines:"
        "\n1. Directly address the given statement and avoid ambiguous interpretations. Stay true to the core topic throughout."
        "\n2. Focus on one main idea and develop it thoroughly. Explain its significance, implications, and how it ties back to the central theme."
        "\n3. Provide relevant examples and evidence to support your points."
        "\n4. Use a variety of sentence structures and maintain a formal tone."
        "\n5. Ensure the paragraph doesn't overlap with other arguments and offers a fresh perspective."
        "\n6. Conclude the paragraph effectively, reinforcing the main idea discussed."
        "\nAim for depth, precision, and utmost relevance. Stay on topic and ensure every point made is pertinent to the central theme."
    )

    return f"{base_prompt}\n\nIn paragraph {paragraph_number}, the statement reads: '{statement}'. Craft a paragraph that contradicts this contention, focusing on a single-threaded, detailed elucidation of the reason specified, ensuring it harmonizes seamlessly with the statement's main theme."

def generate_reasons(statement, choice=None):
    """Generate Supportive and Opposing reasons for a given statement."""
    responses = []

    for paragraph_number in range(1, 3):
        if choice in ('Supportive', None):  # 'None' means generate both Supportive and Opposing
            responses.append(_get_openai_response(statement, 'Supportive', paragraph_number))

        if choice in ('Opposing', None):
            responses.append(_get_openai_response(statement, 'Opposing', paragraph_number))

    return responses

def _get_openai_response(statement, agreement, paragraph_number):
    """Helper function to fetch response from OpenAI API."""
    if agreement == 'Supportive':
        prompt = generate_supportive_prompt(statement, paragraph_number, REASONS_LIST)
    else:
        prompt = generate_opposing_prompt(statement, paragraph_number, REASONS_LIST)

    logger.debug(f"Generated prompt: {prompt}")

    logger.debug("Making OpenAI API call...")
    
    try:
        response = client.chat.completions.create(
            model=ENGINE_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.6
        ).choices[0].message['content'].strip()

        logger.info(f"{agreement} Response for paragraph {paragraph_number}, statement '{statement}': {response}")
    except OpenAIError as e:
        logger.error(f"OpenAI error fetching {agreement} reason: {e}")
        response = "Error: There was an issue with the OpenAI API. Please check your OpenAI plan and billing details."
    except AttributeError as e:
        logger.error(f"AttributeError: {e}")
        response = "Error: Failed to generate reasons due to an AttributeError."
    except Exception as e:
        logger.error(f"Error fetching {agreement} reason: {e}")
        response = "Error: There was an issue with the OpenAI API. Please check your OpenAI plan and billing details."

    return {'title': f'{agreement} reason for paragraph {paragraph_number}:', 'text': response}


def lexicon_count(text, removepunct=False):
    """Count the number of lexicons in the text."""
    if removepunct:
        text = text.translate(str.maketrans('', '', string.punctuation))
    return len(text.split())

def deduct_tokens(user, tokens):
    """Deduct a specified number of tokens from a user."""
    logger.debug(f"Deducting {tokens} tokens from user {user.id}")
    user.tokens -= tokens
    try:
        db.session.commit()
        logger.debug("Token deduction committed successfully.")
    except Exception as e:
        logger.error(f"Error committing token deduction: {str(e)}")
