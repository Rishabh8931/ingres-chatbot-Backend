# app/routers/nlp_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.gemini_service import (
    normalize_query_with_gemini,
    format_back_with_gemini,
)
from app.services.grok_service import(
    normalize_query_with_groq,
    format_back_with_groq

)
from app.services.querryGenerator_service import QueryService 
from app.db.utils import run_sql_query
from app.services.pipeline_service import run_pipeline


router = APIRouter(prefix="/nlp", tags=["NLP"])

class NormalizeRequest(BaseModel):
    text: str

class NormalizeResponse(BaseModel):
    normalized_english: str
    original_language_code: str
    style: str

@router.post("/normalize", response_model=NormalizeResponse)
async def normalize(req: NormalizeRequest):
    try:
        ne, code, style = normalize_query_with_gemini(req.text)
        return {
            "normalized_english": ne,
            "original_language_code": code,
            "style": style,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class FormatBackRequest(BaseModel):
    answer_english: str
    style: str
    original_language_code: str = "unknown"

@router.post("/format-answer")
async def format_answer(req: FormatBackRequest):
    try:
        final_text = format_back_with_gemini(
            answer_english=req.answer_english,
            style=req.style,
            lang_code=req.original_language_code
        )
        return {"final_text": final_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ------------------- SQL Generator -------------------
class SQLExecResponse(BaseModel):
    user_query: str
    generated_sql: str
    db_result: dict

class SQLRequest(BaseModel):
    query: str

@router.post("/to-sql", response_model=SQLExecResponse)
async def query_to_sql(req: SQLRequest):
    """
    Convert user query -> SQL -> Run on DB -> Return result
    """
    try:
       
        sql = QueryService().generate_sql(req.query)
        result = run_sql_query(sql)  # 👈 DB pr run
        return {
            "user_query": req.query,
            "generated_sql": sql,
            "db_result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 

    
# pipeline creation

class NormalizeRequest(BaseModel):
    text: str

class NormalizeResponse(BaseModel):
    result : dict
@router.post("/pipeline", response_model=NormalizeResponse)
async def normalize(req: NormalizeRequest):
    try:
        result = await run_pipeline(req.text)
        return {
           "result" : result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

    