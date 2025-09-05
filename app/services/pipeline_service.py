from app.services.gemini_service import(
    normalize_query_with_gemini_pipeline
)
from app.services.querryGenerator_service import (
    QueryService
)
from app.db.utils import (
   run_sql_query
)



async def run_pipeline(user_query: str):
    # Step 1: send user query → Normalizer service
   normalized_result =  await normalize_query_with_gemini_pipeline(user_query)
    # Step 2: send normalized query → SQL generator
   sql =   QueryService().generate_sql(normalized_result["normalized_english"])
   result = run_sql_query(sql)   # Step 3: run SQL on DB

   return result
   
