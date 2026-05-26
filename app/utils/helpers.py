import datetime

def convert_dates_to_str(obj):
    """Recursively convert all datetime.date objects in a dict/list to ISO-format strings."""
    if isinstance(obj, dict):
        return {k: convert_dates_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_dates_to_str(i) for i in obj]
    elif isinstance(obj, datetime.date):
        return obj.isoformat()
    return obj