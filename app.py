import openai
from flask import Flask, render_template, request, redirect, url_for

import string
import csv

openai.api_key = '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'

app = Flask(__name__)

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

csv_file_path = '/Users/perfectly-imperfect/Documents/GitHub/test/openai-quickstart-python/csv/questions.csv'
examples = read_csv_examples(csv_file_path)

def extract_complete_answer(text, max_words):
    words = text.split()
    if len(words) <= max_words:
        return ' '.join(words)
    else:
        extracted_words = words[:max_words]
        for i in range(max_words-1, -1, -1):
            if extracted_words[i][-1] in {'.', '?', '!'}:
                return ' '.join(extracted_words[:i+1])
        return ' '.join(extracted_words)


def generate_reasons(question):
    supporting_prompt = f"Pretend you are an IELTS Writing examiner who can explain one idea specifically and logically. Show logical progression between sentences. Write one idea to support this argument, using only 200 words and avoiding sophisticated vocabulary.\n\nFor the question: '{question}', provide a supporting reason."
    
    try:
        supporting_response = openai.Completion.create(engine='text-davinci-003', prompt=supporting_prompt, max_tokens=200).choices[0].text.strip()
        # Use extract_complete_answer function to limit the length of the response
        supporting_response = extract_complete_answer(supporting_response, 100)  
        supporting_response = supporting_response.capitalize()  # Only capitalize the first letter
    except Exception as e:
        print("Error generating supporting response: ", e)
        supporting_response = "Error generating supporting response"

    opposing_prompt = f"Pretend you are an IELTS Writing examiner who can explain one idea specifically and logically. Show logical progression between sentences. Write one idea to oppose this argument, using only 200 words and avoiding sophisticated vocabulary.\n\nFor the question: '{question}', provide an opposing reason."
    
    try:
        opposing_response = openai.Completion.create(engine='text-davinci-003', prompt=opposing_prompt, max_tokens=200).choices[0].text.strip()
        # Use extract_complete_answer function to limit the length of the response
        opposing_response = extract_complete_answer(opposing_response, 100)  
        opposing_response = opposing_response.capitalize()  # Only capitalize the first letter
    except Exception as e:
        print("Error generating opposing response: ", e)
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
    random_example = random.choice(examples)
    question = random_example[0]
    supportive_answer = random_example[1]
    opposing_answer = random_example[2]
    return render_template('form.html', feedback_message=feedback_message, question=question, supportive_answer=supportive_answer, opposing_answer=opposing_answer)

@app.route('/generate', methods=['POST'])
def generate():
    question = request.form['question']
    reasons = generate_reasons(question)
    
    # Verify that each reason's text is a string and not a method
    for reason in reasons:
        print(f"{reason['title']} -> {reason['text']}")  # Print out each reason for debugging
    
    return render_template('results.html', reasons=reasons, question=question)


@app.route('/generate_variation', methods=['POST'])
def generate_variation():
    question = request.form['question']
    reasons = generate_reasons(question)
    return render_template('results.html', reasons=reasons, question=question)


@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    rating = request.form['rating']
    feedback = request.form['feedback']
    
    # Save the feedback to the file
    with open('feedback.txt', 'a') as file:
        file.write(f"Rating: {rating}\nFeedback: {feedback}\n\n")
    
    # Redirect back to the main page with a thank you message
    return render_template('form.html', feedback_message='Thank you for your feedback!')

if __name__ == '__main__':
    app.run(debug=True)
