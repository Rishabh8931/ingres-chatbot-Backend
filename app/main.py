# app/main.py
from fastapi import FastAPI
from app.routers import groundwater
from app.routers import nlp_router
from app.db.session import test_db_connection
from contextlib import asynccontextmanager

app = FastAPI(title="Groundwater AI Bot")

# include router
app.include_router(groundwater.router)
app.include_router(nlp_router.router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    test_db_connection()
    yield
    # Shutdown code (if needed)
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"message": "Groundwater AI Bot Backend is running 🚀"}
