import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"

response = requests.get(url)

if response.status_code == 200:
    models = response.json()
    print("Available models with your key:\n")
    for m in models.get("models", []):
        print("-", m["name"])
else:
    print("Error:", response.status_code, response.text)
