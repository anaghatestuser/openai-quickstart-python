from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# List all models
response = client.models.list()

# Print the list of models
for model in response.data:
    print(model['id'])
