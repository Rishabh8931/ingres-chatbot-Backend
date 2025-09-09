# app/routers/nlp_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.pipeline_service import run_pipeline

router = APIRouter(prefix="/nlp", tags=["NLP"])

    
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
    

    