from sqlalchemy import text
from app.db.session import SessionLocal

def run_sql_query(sql: str):
    """
    Run raw SQL and return results as dict (columns + rows).
    """
    session = SessionLocal()
    try:
        result = session.execute(text(sql))
        rows = [list(row) for row in result.fetchall()]
        columns = result.keys()
        return {"columns": list(columns), "rows": rows}
    except Exception as e:
        raise Exception(f"SQL Execution Error: {e}")
    finally:
        session.close()
