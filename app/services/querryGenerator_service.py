from app.utils import config_util
import logging

_MODEL_ = "gemini-2.5-flash"

class QueryService:
    def __init__(self):
        try:
            self.model = config_util.get_gemini_model()
        except Exception as e:
            logging.error(f"[QueryService INIT ERROR] Failed to get Gemini model: {e}")
            raise RuntimeError(f"Cannot initialize QueryService: {e}")

    def generate_sql(self, query: str) -> str:
        """
        Generates PostgreSQL query using Gemini LLM.
        Ensures consistent column aliases for normalization.
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
2. Always use fixed column aliases in SELECT:
   - state_name AS state
   - city_name AS city (only if query is city-specific)
   - parameter_name AS parameter_name
   - unit AS unit
   - year AS year
   - AVG(yd.value) AS value   (for state-level aggregation)
   - yd.value AS value        (for city-level queries)
3. If the user asks for general "groundwater data" without specifying a parameter, 
   then return all parameters ("Groundwater Level", "Water Recharged", "Rainfall", "Exploitation").
4. If query mentions only a STATE (no specific city), calculate the average of all its cities per year per parameter.
   - GROUP BY state, year, parameter_name, unit
5. If query mentions a CITY, return that city’s yearly data (no GROUP BY needed, except for year, parameter_name, unit if multiple rows).
6. If query mentions multiple STATES, compare them by applying Rule #4 for each state.
7. If query mentions multiple CITIES across states, compare them by their yearly data.
8. Always use ILIKE for case-insensitive matching of state_name, city_name, and parameter_name.
9. If query specifies a year range, return yearly breakdown (GROUP BY year, parameter_name, unit, state[, city]).
10. If only one year is given then return only that year's data.
11. Output must be pure SQL string (no markdown, no explanation, no ```sql).

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
            return ""
