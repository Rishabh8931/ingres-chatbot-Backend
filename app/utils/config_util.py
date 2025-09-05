import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("Please set GOOGLE_API_KEY in .env")

# Gemini config
genai.configure(api_key=GOOGLE_API_KEY)

def get_gemini_model():
    return genai.GenerativeModel("gemini-1.5-flash")
