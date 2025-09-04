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
class SQLRequest(BaseModel):
    user_query: str

class SQLResponse(BaseModel):
    user_query: str
    generated_sql: str

query_service = QueryService()

@router.post("/to-sql", response_model=SQLResponse)
async def query_to_sql(req: SQLRequest):
    """
    Convert user natural query -> SQL using hybrid approach.
    """
    try:
        sql = query_service.generate_sql(req.user_query)
        return {"user_query": req.user_query, "generated_sql": sql}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))