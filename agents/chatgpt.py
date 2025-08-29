
import re
from openai import OpenAI
import json
from time import sleep


with open(os.path.join(os.path.dirname(__file__), "api_key.json"), "r") as file:
    api_key = json.load(file)

client = OpenAI(api_key=api_key["api_key"])

def get_response(prompt):
    response = client.responses.create(
        model="gpt-4.1",
        input=f"{prompt}"
    )

    return response.output_text