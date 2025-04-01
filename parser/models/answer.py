from dataclasses import dataclass
from typing import Optional


@dataclass
class MarkScheme:
    def __init__(self, answers: str, guidance: Optional[str]):
        self.answers = answers
        self.guidance = guidance

    def __str__(self):
        output = self.answers
        if self.guidance:
            output += f"\nGuidance: {self.guidance}"
        return output
