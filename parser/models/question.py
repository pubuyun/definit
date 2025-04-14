from dataclasses import dataclass
from typing import List, Optional
from PIL.Image import Image
from .syllabus import Syllabus


@dataclass
class SubSubQuestion:

    def __init__(
        self,
        number: str,
        text: str,
        marks: int = 0,
        answer: Optional[str] = None,
        syllabus: Optional[Syllabus] = None,  # syllabus of the question
    ):
        self.number = number  # roman numeral
        self.text = text
        self.marks = marks
        self.answer = answer

    def __str__(self):
        return self.text


@dataclass
class SubQuestion:

    def __init__(
        self,
        number: str,
        text: str,
        subsubquestions: Optional[List[SubSubQuestion]],
        marks: int = 0,
        answer: Optional[str] = None,
        syllabus: Optional[Syllabus] = None,  # syllabus of the question
    ):
        self.number = number  # a, b, c...
        self.text = text
        self.subsubquestions = subsubquestions
        self.answer = answer
        self.marks = marks

    def __str__(self):
        return self.text + (f"\n{self.subsubquestions}" if self.subsubquestions else "")


@dataclass
class Question:

    def __init__(
        self,
        number: int,
        text: str,
        marks: int = 0,
        subquestions: Optional[List[SubQuestion]] = None,
        answer: Optional[str] = None,
        question_image: Optional[str] = None,  # images in the question
        image: Optional[str] = None,  # image of the whole question
        syllabus: Optional[Syllabus] = None,  # syllabus of the question
    ):
        self.number = number
        self.text = text
        self.subquestions = subquestions
        self.marks = marks
        self.answer = answer
        self.question_image = question_image
        self.image = image

    def __str__(self):
        return f"({self.number}): {self.text}" + (
            f"\n{self.subquestions}" if self.subquestions else ""
        )


@dataclass
class MultipleChoiceQuestion:

    def __init__(
        self,
        number: int,
        text: str,
        options: List[str],
        answer: Optional[str] = None,
        image: Optional[Image] = None,
        syllabus: Optional[Syllabus] = None,  # syllabus of the question
    ):
        self.number = number
        self.text = text
        self.options = options
        self.answer = answer
        self.image = image

    def __str__(self):
        return f"({self.number}): {self.text}" + (
            f"\n{self.options}" if self.options else ""
        )
