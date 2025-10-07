import os
import requests
from dotenv import load_dotenv

# Load API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Pick a valid model from your list
model = "gemini-1.5-flash"   # or "gemini-1.5-pro"

url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"

# Request payload
data = {
    "contents": [
        {"parts": [{"text": "Give me a fun travel tip for visiting Toronto"}]}
    ]
}

response = requests.post(url, json=data)

if response.status_code == 200:
    result = response.json()
    print("\n Gemini API Response:")
    print(result["candidates"][0]["content"]["parts"][0]["text"])
else:
    print("\n Error:", response.status_code, response.text)
