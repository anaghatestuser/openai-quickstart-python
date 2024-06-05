import openai

openai.api_key = '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'

# Set the OpenAI API key

# Fine-tuned model ID
fine_tuned_model_id = 'ft:gpt-3.5-turbo-0125:kiss-academy::9WZvghWM'

# Generate a response using the fine-tuned model
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are an expert IELTS writing assistant. Your task is to provide high-quality, Band 9 level responses for IELTS Writing Task 2. Ensure your responses are well-structured, clear, and directly address the prompt. Focus on one main idea and expand upon it in detail."},
        {"role": "user", "content": "Some people think that children should learn arts at school. Provide a supportive answer focusing on one main idea."}
    ],
    max_tokens=150
)

# Print the response
print(response.choices[0].message['content'].strip())
