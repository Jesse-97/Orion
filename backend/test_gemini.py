# test_gemini.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY")
print(f"Key loaded: {key[:8]}...{key[-4:] if key else 'MISSING'}")

genai.configure(api_key=key)

# List available models to confirm key works
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(m.name)