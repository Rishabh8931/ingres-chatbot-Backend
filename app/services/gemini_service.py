# app/services/gemini_service.py
from typing import Tuple
from app.utils import config_util, extract_json_util
import logging

_MODEL = "gemini-2.5-flash"

# ----- SYSTEM PROMPTS -----
_NORMALIZE_PROMPT = """You are a multilingual query normalizer. And also a helper of an chat-bot that analyses the groundwater level,rainfall,groundwater exploitation, gw-recharge,etc.
TASK: There are multiple type of querries can ask an user like personal to the chatbot like "hi, hello,  chatting with bot,how you can help,etc.' and other one is about the real querry (real work of the bot)or(bussiness querry) like :- 'what is waterlevel of ayodhya in uttarpradesh, compare the rainfall and recharge between two states'. So Convert ANY user query (English, Hindi, Hinglish, or other) into clean English.

RULES:
1. Always return STRICT JSON ONLY. Nothing else.
2. JSON schema:
{
  "normalized_english": "<one-line clean English>",
  "original_language_code": "<BCP47/ISO639-1 if known else 'unknown'>",
  "style": "detect the user's query's language",
  "type": "*required* identify the user's querry intention personal or bussiness"
}
3. Never explain, never add extra keys.
4. Values must NOT contain newlines.
5. If query is vague, still guess best English.
6. use numeric same as given by user.

#Important:- style and type should be correct, so answer precisely, specially work on sanskrit and hinglish language carefully, you are not able to detect hinglish language so please analyse the hinglish language correctly.
# NOTE:- "behave like professional, don't use informal language "

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

=> Important :- use numeric same as given by user.

Return RAW TEXT only, no JSON, no preface.
""" 

# ----- HELPER -----
def _generate(model: str, prompt: str, user_input: str) -> str:
    """
    Safe wrapper to generate content from Gemini model.
    Raises RuntimeError with clear message on failure.
    """
    try:
        model = config_util.get_gemini_model()
        resp = model.generate_content([prompt, user_input])
    except Exception as e:
        logging.error(f"[Gemini ERROR] Failed to generate content: {e}")
        raise RuntimeError(f"Failed to generate content: {e}")

    # Check for blocked responses
    if hasattr(resp, "prompt_feedback") and resp.prompt_feedback and getattr(resp.prompt_feedback, "block_reason", None):
        reason = resp.prompt_feedback.block_reason
        logging.warning(f"[Gemini BLOCKED] {reason}")
        raise RuntimeError(f"Gemini blocked: {reason}")

    # Check if candidates exist
    if not getattr(resp, "candidates", None):
        logging.warning("[Gemini WARNING] No candidates returned.")
        raise RuntimeError("No candidates from Gemini.")

    return getattr(resp, "text", "").strip() or user_input

# ----- MAIN FUNCTIONS -----
def normalize_query_with_gemini(user_query: str) -> Tuple[str, str, str]:
    try:
        raw = _generate(_MODEL, _NORMALIZE_PROMPT, user_query)
        data = extract_json_util.extract_json(raw)
        ne = data.get("normalized_english", user_query).strip()
        code = data.get("original_language_code", "unknown").strip()
        style = data.get("style", "english").strip().lower()
        return ne, code, style
    except Exception as e:
        logging.error(f"[DEBUG] normalize_query_with_gemini fallback: {e}\nRaw: {user_query}")
        return user_query, "unknown", "english"

async def normalize_query_with_gemini_pipeline(user_query: str) -> dict:
    """
    Async-friendly pipeline version.
    """
    try:
        # Currently _generate is sync, so just call normally.
        raw = _generate(_MODEL, _NORMALIZE_PROMPT, user_query)
        data = extract_json_util.extract_json(raw)
        return {
            "normalized_english": data.get("normalized_english", user_query).strip(),
            "original_language_code": data.get("original_language_code", "unknown").strip(),
            "style": data.get("style", "english").strip().lower()
        }
    except Exception as e:
        logging.error(f"[DEBUG] normalize_query_with_gemini_pipeline fallback: {e}\nRaw: {user_query}")
        return {
            "normalized_english": user_query,
            "original_language_code": "unknown",
            "style": "english"
        }

def format_back_with_gemini(answer_english: str, style: str, lang_code: str) -> str:
    payload = f"""original_style: {style}
original_language_code: {lang_code}
answer_english: {answer_english}"""
    try:
        return _generate(_MODEL, _FORMAT_BACK_PROMPT, payload)
    except Exception as e:
        logging.error(f"[DEBUG] format_back_with_gemini fallback: {e}")
        return answer_english  # fallback to plain English
