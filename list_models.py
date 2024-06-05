import openai

openai.api_key = "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"

# List all models
response = openai.Model.list()

# Print the list of models
for model in response['data']:
    print(model['id'])
