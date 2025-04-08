import pymongo
from pymongo import MongoClient
from parser.models.question import Question, SubQuestion, SubSubQuestion
from typing import Any, Dict, List, Optional


def jsonize(obj: Any) -> Dict[str, Any]:
    """
    Recursively converts an object to a JSON-serializable format.
    """
    if isinstance(obj, list):
        return [jsonize(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: jsonize(value) for key, value in obj.items()}
    elif hasattr(obj, "__dict__"):
        return jsonize(obj.__dict__)
    else:
        return obj
