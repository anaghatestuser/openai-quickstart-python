import csv
import os
import openai
from flask import Flask, render_template, request
import string
import smtplib
from email.mime.text import MIMEText
OPENAI_API_KEY='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'

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

def read_csv(file_path):
    data = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        headers = next(reader)  # Read the header row
        for row in reader:
            data.append(row)  # Add each row to the data list
    return data
csv_data = read_csv('/Users/perfectly-imperfect/Documents/GitHub/test/openai-quickstart-python/csv/questions.csv')
print(csv_data)


def lexicon_count(text, removepunct=False):
    if removepunct:
        # Remove punctuation from the text
        text = text.translate(str.maketrans('', '', string.punctuation))

    # Split the text into words and count them
    return len(text.split())

def generate_reasons(question):
    # Personality prompt
    personality_prompt = "Pretend you are an IELTS Writing examiner who are capable of explain one idea specifically and logically. You need to  show logical progression between sentences. Write one idea to support this argument. and a different idea to oppose this argument. Each idea is ONLY 100 words. Please avoid using sophisticated words."

    # Create a prompt that includes the question and the examiner's personality
    supporting_prompt = f"{personality_prompt}\n\nHello! I'm here to help you with your question.\n\nFor the question: '{question}', please provide a supporting reason."

    # Generate supporting reason
    supporting_reason = openai.Completion.create(engine='davinci', prompt=supporting_prompt, max_tokens=200).choices[0].text.strip()

    # Check if the word count is exactly 100 and adjust if necessary
    if lexicon_count(supporting_reason, removepunct=True) > 100:
        supporting_reason = ' '.join(supporting_reason.split()[:100])
        supporting_reason = supporting_reason.rsplit('.', 1)[0] + '.'

    # Create a prompt for opposing reason
    opposing_prompt = f"{personality_prompt}\n\nHello! I'm here to help you with your question.\n\nFor the question: '{question}', please provide an opposing reason."

    # Generate opposing reason
    opposing_reason = openai.Completion.create(engine='text-davinci-002', prompt=opposing_prompt, max_tokens=200).choices[0].text.strip()

    # Check if the word count is exactly 100 and adjust if necessary
    if lexicon_count(opposing_reason, removepunct=True) > 100:
        opposing_reason = ' '.join(opposing_reason.split()[:100])
        opposing_reason = opposing_reason.rsplit('.', 1)[0] + '.'

    # Combine supporting and opposing reasons into one response
    response = f"Hello! I'm here to help you with your question.\n\nFor the question: '{question}', here are my reasons to support and oppose this argument:\n\nSupporting reason:\n\n{supporting_reason}\n\nOpposing reason:\n\n{opposing_reason}"

    return response


@app.route('/', methods=['GET'])
def home():
    return render_template('form.html')

@app.route('/generate', methods=['POST'])
def generate():
    question = request.form['question']
    reasons = generate_reasons(question)
    reasons = reasons.split("\n\n")
    reasons = "<p>" + "</p><p>".join(reasons) + "</p>"
    return render_template('results.html', reasons=reasons, question=question)


@app.route('/generate_variation', methods=['POST'])
def generate_variation():
    question = request.form['question']
    reasons = generate_reasons(question)  # Assuming you have added the 'variation' parameter in your 'generate_reasons' function
    reasons = reasons.split("\n\n")
    reasons = "<p>" + "</p><p>".join(reasons) + "</p>"
    return render_template('results.html', reasons=reasons, question=question)

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    rating = request.form['rating']
    feedback = request.form['feedback']
    # Here, you can do something with the feedback. For example, you can store it in a database, 
    # or write it to a file, or send it to an API for further analysis. 
    return 'Thank you for your feedback!'


if __name__ == '__main__':
    app.run(debug=True)
