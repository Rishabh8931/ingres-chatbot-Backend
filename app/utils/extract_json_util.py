
import re
import json

def extract_json(raw: str) -> dict:
    """Ensure we extract valid JSON object even if model adds noise."""
    try:
        return json.loads(raw)
    except:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError(f"Could not parse JSON from: {raw}")