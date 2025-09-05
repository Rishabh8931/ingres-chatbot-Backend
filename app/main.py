# app/main.py
from fastapi import FastAPI,HTTPException
from app.routers import groundwater
from app.routers import nlp_router
from app.db.session import test_db_connection
from contextlib import asynccontextmanager






@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    test_db_connection()
    yield
    # Shutdown code (if needed)
    print("Shutting down...")

app = FastAPI(lifespan=lifespan,
              title= "Groundwater Ai bot"

              )
# include router
app.include_router(groundwater.router)
app.include_router(nlp_router.router)

@app.get("/")
def root():
    return {"message": "Groundwater AI Bot Backend is running 🚀"}


