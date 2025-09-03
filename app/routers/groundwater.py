from fastapi import APIRouter

router = APIRouter(
    prefix="/groundwater",
    tags=["Groundwater"]
)

@router.get("/test")
def test_groundwater():
    return {"message": "Groundwater router working ✅"}
