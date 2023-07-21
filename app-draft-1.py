import os
import openai
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_reasons(question):
    prompt = f"In some cities, there are few controls over the design and construction of new homes and office buildings, so people can build in whatever style they like. One reason to support this argument is: {openai.Completion.create(engine='davinci', prompt=question, max_tokens=100).choices[0].text} On the other hand, one reason to oppose this argument is: {openai.Completion.create(engine='davinci', prompt=question, max_tokens=100).choices[0].text}"
    return prompt

@app.route('/', methods=['GET'])
def home():
    return render_template('form.html')

@app.route('/generate', methods=['POST'])
def generate():
    question = request.form['question']
    reasons = generate_reasons(question)
    reasons = reasons.replace("\\n", "<br>")
    return render_template('results.html', reasons=reasons)


if __name__ == '__main__':
    app.run(debug=True)


