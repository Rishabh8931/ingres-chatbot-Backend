# app/pipeline/run_pipeline.py
import logging
from app.services.gemini_service import (
    normalize_query_with_gemini_pipeline,
    format_back_with_gemini
)
from app.services.querryGenerator_service import QueryService
from app.db.utils import run_sql_query
from app.services.explaination_sercvice import generate_textual_explanation
from app.utils.senitize import sanitize_result


async def run_pipeline(user_query: str):
    """
    Pipeline:
    1. Normalize user query (any language → clean English)
    2. Generate SQL
    3. Execute SQL on DB
    4. Generate explanation
    5. Format back to user style
    6. Return both raw results + final answer
    """

    # Step 1: Normalize user query
    try:
        normalized_result = await normalize_query_with_gemini_pipeline(user_query)
        normalized_query = normalized_result.get("normalized_english", "").strip()
        if not normalized_query:
            logging.warning("[Pipeline WARNING] Normalized query is empty. Using original query.")
            normalized_query = user_query
    except Exception as e:
        logging.error(f"[Pipeline ERROR] Normalization failed: {e}")
        normalized_query = user_query
        normalized_result = {"style": "formal", "original_language_code": "en"}

    # Step 2: Generate SQL
    try:
        sql = QueryService().generate_sql(normalized_query)
        logging.info(f"[Pipeline SQL] Generated: {sql}")
        if not sql:
            return {
                "message": "Sorry, data not found",
                "results": None,
                "final_answer": None,
            }
    except Exception as e:
        logging.error(f"[Pipeline ERROR] SQL generation failed: {e}")
        return {
            "message": "Sorry, data not found",
            "results": None,
            "final_answer": None,
        }

    # Step 3: Execute SQL
    try:
        result = run_sql_query(sql)
        result = sanitize_result(result)
        if not result or (isinstance(result, dict) and not result.get("rows")):
            logging.info("[Pipeline INFO] Query returned no rows.")
            return {
                "message": "Sorry, data not found",
                "results": [],
                "final_answer": None,
            }
    except Exception as e:
        logging.error(f"[Pipeline ERROR] Database query failed: {e}")
        return {
            "message": "Sorry, database query failed",
            "results": None,
            "final_answer": None,
        }

    # Step 4: Explanation
    try:
        textual_explanation = generate_textual_explanation(normalized_query, result)
    except Exception as e:
        logging.error(f"[Pipeline ERROR] Explanation generation failed: {e}")
        textual_explanation = "Sorry, explanation could not be generated"

    # Step 5: Format back to user style
    try:
        final_answer = format_back_with_gemini(
            textual_explanation,
            normalized_result.get("style", "formal"),
            normalized_result.get("original_language_code", "en"),
        )
    except Exception as e:
        logging.error(f"[Pipeline ERROR] Formatting failed: {e}")
        final_answer = "Sorry, explanation could not be generated"

    # ✅ Final response with both
    return {
        "results": result,          # raw DB query output
        "final_answer": final_answer,  # AI generated explanation/answer
    }
