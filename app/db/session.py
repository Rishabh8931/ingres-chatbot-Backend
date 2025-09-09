from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")



# Create engine
engine = create_engine(DATABASE_URL, echo=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to test DB connection
def test_db_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))  # simple test query
        print("✅ DB Connected!")
    except Exception as e:
        print("❌ DB Connection Failed:", e)

# Dependency for FastAPI endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
