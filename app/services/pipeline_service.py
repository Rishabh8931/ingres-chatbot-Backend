# app/pipeline/run_pipeline.py
import logging
from app.services.gemini_service import (
    normalize_query_with_gemini_pipeline,
    format_back_with_gemini
)
from app.services.querryGenerator_service import QueryService
from app.db.utils import run_sql_query
from app.services.explaination_sercvice import generate_textual_explanation

async def run_pipeline(user_query: str):
    """
    Pipeline:
    1. Normalize user query (any language → clean English)
    2. Generate SQL
    3. Execute SQL on DB
    4. Return results with proper error handling
    """

    # Step 1: Normalize user query
    try:
        normalized_result = await normalize_query_with_gemini_pipeline(user_query)
        normalized_query = normalized_result.get("normalized_english", "").strip()
        if not normalized_query:
            logging.warning(f"[Pipeline WARNING] Normalized query is empty. Using original query.")
            normalized_query = user_query
    except Exception as e:
        logging.error(f"[Pipeline ERROR] Normalization failed: {e}")
        normalized_query = user_query

    # Step 2: Generate SQL
    try:
        print(normalized_result)
        sql =   QueryService().generate_sql(normalized_query)
        if not sql:
            logging.warning(f"[Pipeline WARNING] SQL generation returned empty. Returning data not found.")
            return {"message": "Sorry, data not found"}
    except Exception as e:
        logging.error(f"[Pipeline ERROR] SQL generation failed: {e}")
        return {"message": "Sorry, data not found"}

    # Step 3: Execute SQL
    try:
        result = run_sql_query(sql)
        if not result or (isinstance(result, dict) and not result.get("rows")):
            logging.info(f"[Pipeline INFO] Query returned no rows.")
            return {"message": "Sorry, data not found"}
    except Exception as e:
        logging.error(f"[Pipeline ERROR] Database query failed: {e}")
        return {"message": "Sorry, data not found"}
  
    

# explaining the threat

    try:
        
        textual_explanation =  generate_textual_explanation(normalized_query,result)
    except Exception as e:
        logging.error(f"[Pipeline ERROR] Explanation generation failed: {e}")
        return {"message": "Sorry, explanation could not be generated"}
    
        
## formatting back
    try:
        
        final_answer = format_back_with_gemini(textual_explanation,normalized_result["style"],normalized_result["original_language_code"])
        return {"final_answer" : final_answer}
    except Exception as e:
        logging.error(f"[Pipeline ERROR] Explanation generation failed: {e}")
        
        return {"message": "Sorry, explanation could not be generated"}
    
        