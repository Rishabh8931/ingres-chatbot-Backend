from decimal import Decimal

def sanitize_result(result):
    """
    Convert Decimal to float so JSON serialization & AI explanation works.
    """
    if isinstance(result, dict):
        sanitized = {}
        for k, v in result.items():
            if isinstance(v, list):
                sanitized[k] = [sanitize_result(x) for x in v]
            else:
                sanitized[k] = float(v) if isinstance(v, Decimal) else v
        return sanitized
    elif isinstance(result, list):
        return [sanitize_result(x) for x in result]
    elif isinstance(result, Decimal):
        return float(result)
    return result
