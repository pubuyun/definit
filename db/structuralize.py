import json
from parser.models.question import Question, SubQuestion, SubSubQuestion
from typing import List, Dict, Any, Optional


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


if __name__ == "__main__":
    # Example usage
    question = Question(
        number=1,
        text="What is the capital of France?",
        subquestions=[
            SubQuestion(
                number="a",
                text="Paris",
                subsubquestions=[SubSubQuestion(number="i", text="Correct answer")],
            )
        ],
    )

    # Convert to JSON-serializable format
    json_data = jsonize(question)

    # Print the JSON data
    print(json.dumps(json_data, indent=4))
