

from app.utils import(
    config_util
)




def explain_with_gemini(data: dict, query: str, original_language_style: str, code: str = None):
    prompt = f"""
    You are an assistant. User provided:
    - Data (JSON): {data}
    - Query: {query}
    - Code: {code if code else "No code provided"}
    - Language style: {original_language_style}

    Task:
    1. Understand the query and data.
    2. If code is given, explain it also.
    3. Answer in {original_language_style}.
    4. Output must be clear **bullet points**.
    """

    response = config_util.get_gemini_model( ).generate_content(prompt)
    return response.text.split("\n")  # split so frontend me bullet points ban sake
