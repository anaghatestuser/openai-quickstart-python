import os
import nltk
import string
import openai
import logging
import random
from config import db  # Import the db object from your config module

# Setting up logging
logger = logging.getLogger(__name__)

# Configuration setup
ENGINE_NAME = os.environ.get('OPENAI_ENGINE_NAME', 'text-davinci-003')
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
    return capitalize_first_letter(' '.join(extracted_words))


REASONS_LIST = [
    "creativity", "critical thinking", "empathy", "face-to-face communication skills", "better memory of content", 
    "concentration", "accountability", "motivation", "physical health", "belonging", "self-esteem", "identity", "lonely", 
    "feeling connected", "feeling secure", "efficient work", "efficient study", "efficient life", "earning more money", 
    "happy", "feel stressed", "feel relaxed", "good environment", "sustainable development", "less crimes", "cultural identity", 
    "social cohesion", "economic growth", "competitive work environment", "schools too much focus on academic study", 
    "boring content", "interesting content", "gender stereotypes", "practical skills", "technology development", "media influence", 
    "urbanisation", "overuse natural resources", "government focus too much on economic growth"
    ]

def generate_prompt(statement, agreement, paragraph_number, reasons=None):
    """Generate a prompt for generating Supportive/Opposing paragraphs for IELTS writing task."""
    
    seeding_reason = f"Anchor your exposition around the reason: '{random.choice(reasons)}'. This reason should directly and unequivocally resonate with the core statement. " if reasons else ""
    
    base_prompt = (
        f"You're tasked with simulating an IELTS Band 9 Writing Task 2 response. {seeding_reason}"
        "To achieve this standard, compose a 120-word paragraph adhering to these guidelines:"
        "\n1. Address the given statement directly and avoid ambiguous interpretations. Stay true to the core topic throughout."
        "\n2. Elaborate deeply on the given reason. Explain its significance, implications, and 'how' it ties back to the central theme. If introducing sub-points, ensure they seamlessly weave into the main reason."
        "\n3. Ensure the paragraph doesn't overlap with other arguments, and offers a fresh perspective."
        "\n4. Maintain a balanced and precise exposition, refraining from unnecessary elaborations."
        "\nAim for depth, precision, and utmost relevance. Stay on topic and ensure every point made is pertinent to the central theme."
    )

    action_word = "supports" if agreement == "Supportive" else "contradicts"
    return f"{base_prompt}\n\nIn paragraph {paragraph_number}, the statement reads: '{statement}'. Craft a paragraph that {action_word} this contention, focusing on a single-threaded, detailed elucidation of the reason specified, ensuring it harmonizes seamlessly with the statement's main theme."

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
    prompt = generate_prompt(statement, agreement, paragraph_number, REASONS_LIST)
    print("Making OpenAI API call...")
    
    try:
        response = openai.Completion.create(
            engine=ENGINE_NAME,
            prompt=prompt,
            max_tokens=200,
            n=1,
            stop=".\\n\\n",
            temperature=0.6
        ).choices[0].text.strip()

        logger.info(f"{agreement} Response for paragraph {paragraph_number}, statement '{statement}': {response}")

    except Exception as e:
        logger.error(f"Error fetching {agreement} reason: {e}")
        response = extract_complete_answer(response, 120)
        response = capitalize_first_letter(response)

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
