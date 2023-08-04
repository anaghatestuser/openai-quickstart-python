import nltk
import string
import openai
import logging
from config import db  # Import the db object from your config module

logger = logging.getLogger(__name__)

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

def generate_prompt(question, agreement):
    return (
        f"Pretend you are an IELTS Band 9 Writing Task 2 examiner who is capable of writing a 120 words paragraph. "
        f"ONLY discuss ONE reason to {agreement} with a statement. The reason should be one of the following: "
        f"creativity, critical-thinking, empathy, face-to-face communication skills, better memory of content, "
        f"concentration, accountability, motivation, physical health, belonging, self-esteem, identity, lonely, "
        f"feel connected, feel secure, efficient work, efficient study, efficient life, earn more money, happy, "
        f"feel stressed, feel relaxed, good environment, sustainable development, less crimes, cultural identity, "
        f"social cohesion, economic growth. Write this reason clearly in the first sentence, explain it specifically, "
        f"logically, and sufficiently with a clear logical progression. Avoid using 'Although', 'but', 'However', "
        f"and sophisticated words. \n\nFor the question: '{question}', provide a {agreement} reason."
    )

def generate_reasons(question):
    try:
        supporting_prompt = generate_prompt(question, 'agree')
        supporting_response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=supporting_prompt,
            max_tokens=200,
            n=1,
            stop=".\\n\\n",
            temperature=0.6
        ).choices[0].text.strip()
        supporting_response = extract_complete_answer(supporting_response, 100)
        supporting_response = capitalize_first_letter(supporting_response)

        logger.info(f"Supporting Response for question '{question}': {supporting_response}")
    except Exception as e:
        logger.error(f"Error generating supporting response for question '{question}': {str(e)}")
        supporting_response = "We're sorry, but we can't generate a supporting response at the moment. Please try again and we will try our best to get you the right response."

    try:
        opposing_prompt = generate_prompt(question, 'disagree')
        opposing_response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=opposing_prompt,
            max_tokens=200,
            n=1,
            stop=".\\n\\n",
            temperature=0.6
        ).choices[0].text.strip()
        opposing_response = extract_complete_answer(opposing_response, 100)
        opposing_response = capitalize_first_letter(opposing_response)

        logger.info(f"Opposing Response for question '{question}': {opposing_response}")
    except Exception as e:
        logger.error(f"Error generating opposing response for question '{question}': {str(e)}")
        opposing_response = "We're sorry, but we can't generate an opposing response at the moment. Please try again and we will try our best to get you the right response."

    return [
        {'title': 'Supporting reason:', 'text': supporting_response},
        {'title': 'Opposing reason:', 'text': opposing_response}
    ]

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
