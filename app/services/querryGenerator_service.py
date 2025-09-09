# app/services/query_service.py
from app.utils import config_util
import logging

_MODEL_ = "gemini-2.5-flash"

class QueryService:
    def __init__(self):
        try:
            self.model = config_util.get_gemini_model( )
        except Exception as e:
            logging.error(f"[QueryService INIT ERROR] Failed to get Gemini model: {e}")
            raise RuntimeError(f"Cannot initialize QueryService: {e}")

    def generate_sql(self, query: str) -> str:
        """
        Generates PostgreSQL query using Gemini LLM.
        Returns safe SQL string even on failure (fallback: empty string).
        """
        prompt = f"""
You are an expert PostgreSQL query generator. 
The database schema is:

TABLE states (
  state_id SERIAL PRIMARY KEY,
  state_name VARCHAR(100)
);

TABLE cities (
  city_id SERIAL PRIMARY KEY,
  city_name VARCHAR(100),
  state_id INT REFERENCES states(state_id)
);

TABLE parameters (
  parameter_id SERIAL PRIMARY KEY,
  parameter_name VARCHAR(100), -- values: 'Groundwater Level', 'Water Recharged', 'Rainfall', 'Exploitation'
  unit VARCHAR(50)
);

TABLE yearly_data (
  data_id SERIAL PRIMARY KEY,
  city_id INT REFERENCES cities(city_id),
  parameter_id INT REFERENCES parameters(parameter_id),
  year INT,
  value FLOAT
);

RULES:
1. Always join all four tables correctly: yearly_data → cities → states → parameters.
2. If the user asks for general "groundwater data" without specifying a parameter, 
   then return all parameters ("Groundwater Level", "Water Recharged", "Rainfall", "Exploitation").
3. If query mentions only a STATE (no specific city), calculate the average of all its cities per year per parameter.
   - GROUP BY year, parameter_name, and unit.
4. If query mentions a CITY, return that city’s yearly data (for the requested parameter(s)).
5. If query mentions multiple STATES, compare them by applying Rule #3 for each state.
   - The result should contain year, state, parameter_name, avg_value, and unit.
6. If query mentions multiple CITIES across states, compare them by their yearly data.
7. Always use ILIKE for case-insensitive matching of state_name, city_name, and parameter_name.
8. If query specifies a year range, return yearly breakdown (GROUP BY yd.year, parameter_name, unit).
9. If year range not given then give data for all years for requested state or city.
10. If only one year is given then give only for that year as required params.
11. Always include `unit` from parameters and years table in SELECT.
12. Return only valid SQL (no markdown, no explanation, no ```sql).

User query: {query}
"""

        try:
            response = self.model.generate_content(prompt)
            sql = getattr(response, "text", "").strip()

            # Remove possible markdown or backticks safely
            if sql.startswith("```"):
                sql = sql.split("\n", 1)[-1]  # remove first line ```sql or ```
                sql = sql.rsplit("```", 1)[0].strip()

            return sql

        except Exception as e:
            logging.error(f"[QueryService ERROR] Failed to generate SQL for query '{query}': {e}")
            # Fallback: return empty string or raise depending on your preference
            return ""
