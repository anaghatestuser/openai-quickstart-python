import os
import nltk
import string
import openai
import logging
import random 
from config import db  # Import the db object from your config module

# Setting up logging
logger = logging.getLogger(__name__)

# Retrieves the value of OPENAI_ENGINE_NAME from the .env and defaults to 'text-davinci-003' if it's not set.
ENGINE_NAME = os.environ.get('OPENAI_ENGINE_NAME', 'text-davinci-003')

# Check environment and set nltk data path
is_on_render = os.environ.get('IS_ON_RENDER', 'False').lower() == 'true'
nltk_data_path = os.environ.get('NLTK_DATA_PATH', '/opt/render/project/src/nltk_data') if is_on_render else os.path.expanduser('~/nltk_data')
data_path = os.path.join(nltk_data_path, 'tokenizers/punkt')

# Download punkt tokenizer if not available
if not os.path.exists(data_path):
    nltk.download('punkt', download_dir=nltk_data_path)
nltk.data.path.append(nltk_data_path)

def capitalize_first_letter(text):
    sentences = nltk.sent_tokenize(text)
    capitalized_sentences = [sentence.strip().capitalize() for sentence in sentences]
    return ' '.join(capitalized_sentences)

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
    # This portion adds a random reason from your list to seed the AI.
    seeding_reason = ""
    if reasons:
        seeding_reason = f"Consider reasons like {random.choice(reasons)} but don't limit yourself to them. "
    
    base_prompt = (
        f"Imagine you are an IELTS Band 9 Writing Task 2 examiner. {seeding_reason}"
        f"Your task is to write a 120-word paragraph that fulfills the following requirements:\n"
        f"1. Each paragraph should clearly convey a single idea either supporting or opposing the statement without starting with the phrase 'One reason'.\n"  # Explicit instruction
        f"2. Use different reasons for each paragraph.\n"
        f"3. Ensure the reason is interwoven into the paragraph seamlessly.\n"
        f"4. Explain the reason in a specific, logical, and sufficient manner, with a clear progression of ideas.\n"
        f"5. Incorporate collocations.\n"
        f"6. Do not use words including 'Although', 'but', 'However', 'While'.\n"
        f"7. Refrain from using complex vocabulary.\n"
        f"8. The paragraph must be 120 words in length.\n"
        f"9. Utilize CEFR C1 level words."
    )
    
    if agreement == "support":
        return (
            f"{base_prompt}\n\nFor paragraph {paragraph_number}, the given statement is: '{statement}'. "
            f"Craft a paragraph that advocates for this statement without starting with the phrase 'One reason'."
        )
    else:
        return (
            f"{base_prompt}\n\nFor paragraph {paragraph_number}, the given statement is: '{statement}', "
            f"Construct a paragraph that disputes this statement without leading with the phrase 'One reason'."
        )


def generate_reasons(statement):
    # Use the entire reasons list to seed the AI but don't enforce them.
    responses = []
    for paragraph_number in range(1, 3):
        # Generate supporting prompt and response
        supporting_prompt = generate_prompt(statement, 'support', paragraph_number, REASONS_LIST)
        supporting_response = openai.Completion.create(
            engine=ENGINE_NAME,
            prompt=supporting_prompt,
            max_tokens=200,
            n=1,
            stop=".\\n\\n",
            temperature=0.6
        ).choices[0].text.strip()
        supporting_response = extract_complete_answer(supporting_response, 120)
        supporting_response = capitalize_first_letter(supporting_response)
        logger.info(f"Supporting Response for paragraph {paragraph_number}, statement '{statement}': {supporting_response}")

        # Generate opposing prompt and response
        opposing_prompt = generate_prompt(statement, 'oppose', paragraph_number, REASONS_LIST)
        opposing_response = openai.Completion.create(
            engine=ENGINE_NAME,
            prompt=opposing_prompt,
            max_tokens=200,
            n=1,
            stop=".\\n\\n",
            temperature=0.6
        ).choices[0].text.strip()
        opposing_response = extract_complete_answer(opposing_response, 120)
        opposing_response = capitalize_first_letter(opposing_response)
        logger.info(f"Opposing Response for paragraph {paragraph_number}, statement '{statement}': {opposing_response}")

        responses.extend([
            {'title': f'Supporting reason for paragraph {paragraph_number}:', 'text': supporting_response},
            {'title': f'Opposing reason for paragraph {paragraph_number}:', 'text': opposing_response}
        ])

    return responses



def lexicon_count(text, removepunct=False):
    if removepunct:
        text = text.translate(str.maketrans('', '', string.punctuation))
    return len(text.split())

def deduct_tokens(user, tokens):
    logger.debug(f"Deducting {tokens} tokens from user {user.id}")
    user.tokens -= tokens
    try:
        db.session.commit()
        logger.debug("Token deduction committed successfully.")  # Changed from print to logger.debug
    except Exception as e:
        logger.error("Error committing token deduction: ", e)  # Changed from print to logger.error