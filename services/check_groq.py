import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing. Check your .env file.")

client = Groq(api_key=api_key)

response = client.models.list()

print("Models returned by Groq:")
for model in response.data:
    print(model.id)