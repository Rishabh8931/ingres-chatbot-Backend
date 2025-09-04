import os
import re
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("Please set GOOGLE_API_KEY in .env")

genai.configure(api_key=GOOGLE_API_KEY)


class QueryService:
    """
    Hybrid Query Service:
    - Simple queries → rule-based SQL templates
    - Complex queries → Gemini-generated SQL
    """

    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model = genai.GenerativeModel(model_name)

    def is_simple_query(self, query: str) -> bool:
        comparison_keywords = ["compare", "versus", "vs", "between", "aur", "and"]
        if any(word in query.lower() for word in comparison_keywords):
            return False
        return True

    def handle_simple_query(self, query: str) -> str:
        """
        Rule-based SQL generator for simple queries.
        """
        years = re.findall(r"\b(19|20)\d{2}\b", query)
        start_year, end_year = None, None
        if len(years) >= 2:
            start_year, end_year = years[0], years[1]
        elif len(years) == 1:
            start_year = end_year = years[0]

        # detect state (first Capitalized word)
        match = re.search(r"\b([A-Z][a-z]+)\b", query)
        state = match.group(1) if match else None

        # parameter mapping
        if "level" in query.lower():
            param = "Groundwater Level"
        elif "recharge" in query.lower() or "water" in query.lower():
            param = "Water Recharged"
        elif "rainfall" in query.lower():
            param = "Rainfall"
        elif "exploit" in query.lower() or "extraction" in query.lower():
            param = "Exploitation"
        else:
            param = "Groundwater Level"

        sql = f"""
        SELECT assessment_year, AVG(parameter_value) AS avg_value
        FROM groundwater
        WHERE parameter_name = '{param}'
        """
        if state:
            sql += f" AND state ILIKE '{state}'"
        if start_year and end_year:
            sql += f" AND assessment_year BETWEEN {start_year} AND {end_year}"
        sql += """
        GROUP BY assessment_year
        ORDER BY assessment_year;
        """
        return sql.strip()

    def handle_complex_query(self, query: str) -> str:
        """
        Gemini handles multi-state/multi-city/multi-parameter queries.
        """
        prompt = f"""
You are an expert SQL generator for PostgreSQL.

TABLE: groundwater_db
Columns:
- state (TEXT)
- city (TEXT)
- assessment_year (INT)
- parameter_name (TEXT)  -- values: 'Groundwater Level', 'Water Recharged', 'Rainfall', 'Exploitation'
- parameter_value (FLOAT)
- category (TEXT)

RULES:
1. If query mentions only STATE (no city), return average of all cities in that state per year.
2. If multiple states/cities/parameters are compared, use GROUP BY or CTEs.
3. Always return only one SQL query, nothing else.
4. Use ILIKE for case-insensitive matching.
5. Use GROUP BY assessment_year when averaging states.

User query: {query}
        """.strip()

        response = self.model.generate_content(prompt)
        return response.text.strip()

    def generate_sql(self, query: str) -> str:
        if self.is_simple_query(query):
            return self.handle_simple_query(query)
        else:
            return self.handle_complex_query(query)
