import csv
import openai

openai.api_key = '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'

def extract_complete_answer(text, max_words):
    words = text.split()
    if len(words) <= max_words:
        return text
    else:
        extracted_words = words[:max_words]
        # Find the last complete sentence within the extracted words
        for i in range(max_words-1, -1, -1):
            if extracted_words[i][-1] in {'.', '?', '!'}:
                return ' '.join(extracted_words[:i+1])
        # If no complete sentence is found, return the extracted words as is
        return ' '.join(extracted_words)

def generate_reasons(question):
    supporting_prompt = f"Pretend you are an IELTS Writing examiner who can explain one idea specifically and logically. Show logical progression between sentences. Write one idea to support this argument, using only 200 words and avoiding sophisticated vocabulary.\n\nFor the question: '{question}', provide a supporting reason."

    supporting_reason = openai.Completion.create(engine='text-davinci-003', prompt=supporting_prompt, max_tokens=200).choices[0].text.strip()
    supporting_reason = extract_complete_answer(supporting_reason, 100)

    opposing_prompt = f"Pretend you are an IELTS Writing examiner who can explain one idea specifically and logically. Show logical progression between sentences. Write one idea to oppose this argument, using only 200 words and avoiding sophisticated vocabulary.\n\nFor the question: '{question}', provide an opposing reason."

    opposing_reason = openai.Completion.create(engine='text-davinci-003', prompt=opposing_prompt, max_tokens=200).choices[0].text.strip()
    opposing_reason = extract_complete_answer(opposing_reason, 100)

    response = f"For the question: '{question}', here are my reasons to support and oppose this argument:\n\nSupporting reason:\n\n{supporting_reason}\n\nOpposing reason:\n\n{opposing_reason}"

    return response

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

user_question = input("Please enter your question (or 'q' to quit): ")
while user_question != 'q':
    reasons = generate_reasons(user_question)
    print(reasons)
    user_question = input("Please enter your question (or 'q' to quit): ")
