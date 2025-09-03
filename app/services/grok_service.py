# app/services/groq_service.py
import os
import json
import re
from typing import Tuple
from dotenv import load_dotenv
from groq import Groq  # Groq SDK

load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Model (Groq provides LLaMA 3, Mixtral, Gemma etc.)
_MODEL = "openai/gpt-oss-120b"  # you can also try "mixtral-8x7b-32768"

# ----- SYSTEM PROMPTS -----

_NORMALIZE_PROMPT = """You are a multilingual query normalizer. And also a helper of a chat-bot that analyses the groundwater level,rainfall,groundwater exploitation, gw-recharge,etc.
TASK: There are multiple type of queries an user can ask like personal to the chatbot ("hi, hello, chatting with bot, how you can help, etc.") and business queries ("what is waterlevel of ayodhya in uttarpradesh, compare the rainfall and recharge between two states"). Convert ANY user query (English, Hindi, Hinglish, or other) into clean English.

RULES:
1. Always return STRICT JSON ONLY. Nothing else.
2. JSON schema:
{
  "normalized_english": "<one-line clean English>",
  "original_language_code": "<BCP47/ISO639-1 if known else 'unknown' >",
  "style": "detect the user's query's language, if user ask in hinglish then style should be hinglish ",
   "type": "personal or bussiness querry",
}

3. Never explain, never add extra keys.
4. Values must NOT contain newlines.
5. If query is vague, still guess best English.

#Important:- style and type should be correct, so answer precisely, specially work on sanskrit and hinglish language carefully, you are not able to detect hinglish language so please analyse the hinglish language correctly

User query:"""

_FORMAT_BACK_PROMPT = """You are a multilingual stylist.
Given:
- original_style: one of english, hindi, hinglish, or other-language-name
- original_language_code: BCP47/ISO code (e.g., hi, bn, ta, unknown)
- answer_english: final English answer

Return the final answer adapted to the user's style:
- english → polished English.
- hindi → natural Hindi in Devanagari.
- hinglish → mix of Romanized Hindi + simple English (chat style).
- other-language-name → natural translation to that language.

Return RAW TEXT only, no JSON, no preface.
"""

# ----- HELPER -----

def _generate(model: str, prompt: str, user_input: str) -> str:
    """Send prompt + input to Groq and return the model's text output."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input},
        ],
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def _extract_json(raw: str) -> dict:
    """Ensure we extract valid JSON object even if model adds noise."""
    try:
        return json.loads(raw)
    except:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError(f"Could not parse JSON from: {raw}")


# ----- MAIN FUNCTIONS -----

def normalize_query_with_groq(user_query: str) -> Tuple[str, str, str]:
    raw = _generate(_MODEL, _NORMALIZE_PROMPT, user_query)
    try:
        data = _extract_json(raw)
        ne = data["normalized_english"].strip()
        code = data.get("original_language_code", "unknown").strip()
        style = data.get("style", "english").strip().lower()
        return ne, code, style
    except Exception as e:
        print(f"[DEBUG] Fallback because parsing failed: {e}\nRaw: {raw}")
        return user_query, "unknown", "english"


def format_back_with_groq(answer_english: str, style: str, lang_code: str) -> str:
    payload = f"""original_style: {style}
original_language_code: {lang_code}
answer_english: {answer_english}"""
    return _generate(_MODEL, _FORMAT_BACK_PROMPT, payload)
