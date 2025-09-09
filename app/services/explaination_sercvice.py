# app/services/gemini_service.py
from app.utils import config_util
import logging
import json

_MODEL = "gemini-1.5-flash"



_EXPLANATION_PROMPT = """You are a helpful data assistant.
User Query: {query}
Data: {data}

Task:
1. Analyze the data according to the user query.
2. Extract relevant numbers and insights.
3. Generate a short, clear textual explanation suitable for frontend display.
4. Write in professional, concise, human-readable language.
5. Data that you use for explanation should be in readable form; do NOT use table format.
6. Format the explanation in bullet points, each starting with '- '.
"""



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


# ----- TEXTUAL EXPLANATION GENERATOR -----
def generate_textual_explanation(user_query: str, data: dict) -> str:
    """
    Generate professional textual explanation for given query and tabular data.
    """
    try:
        table_str = json.dumps(data)
        prompt = _EXPLANATION_PROMPT.format(query=user_query, data=table_str)
        explanation = _generate(_MODEL, prompt, user_query)
        return explanation
    except Exception as e:
        logging.error(f"[DEBUG] generate_textual_explanation fallback: {e}\nRaw: {user_query}")
        return "Sorry, couldn't generate explanation."
