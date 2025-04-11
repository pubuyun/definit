from typing import List, Optional


class Syllabus:
    def __init__(self, number: str, title: str, content: List[str] = []):
        self.number = number
        self.title = title
        self.content = content

    def __repr__(self):
        return f"Syllabus(number={self.number}, title={self.title}, content={self.content})"
