import re
from dataclasses import dataclass
import pdfplumber
from enum import StrEnum
from typing import List, Optional, Tuple
import turtle
import pprint


@dataclass
class MarkScheme:
    def __init__(self, answers: List[Tuple[List[str], int]], guidance: Optional[str]):
        self.answers = answers
        self.guidance = guidance

    def __str__(self):
        output = ""
        for answer, mark in self.answers:
            output += f"{answer} [{mark}]\n"
        if self.guidance:
            output += f"Guidance: {self.guidance}"
        return output


@dataclass
class SubSubQuestion:
    def __init__(
        self,
        number: str,
        text: str,
        marks: int = 0,
        answer: Optional[MarkScheme] = None,
    ):
        self.number = number
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
        answer: Optional[MarkScheme] = None,
    ):
        self.number = number
        self.text = text
        self.subsubquestions = subsubquestions
        self.answer = answer
        self.marks = marks

    def __str__(self):
        return self.text + (f"\n{self.subsubquestions}")


@dataclass
class Question:
    def __init__(
        self,
        number: int,
        text: str,
        subquestions: List[SubQuestion],
        marks: int = 0,
        answer: Optional[MarkScheme] = None,
    ):
        self.number = number
        self.text = text
        self.subquestions = subquestions
        self.marks = marks
        self.answer = answer

    def __str__(self):
        return f"({self.number}): {self.text}" + (f"\n{self.subquestions}")


class ParserError(Exception):
    pass


class QuestionPaperParser:
    QUESTION_START_X = 50
    SUBQUESTION_START_X = 72
    SUBSUBQUESTION_STARTS = [
        ("i", 96),
        ("ii", 93),
        ("iii", 90),
        ("iv", 90),
        ("v", 93),
        ("vi", 90),
    ]
    IGNORE_PAGE_FOOTER_Y = 35
    PAGE_NUMBER_Y = 790.4778
    LAST_PAGE_COPYRIGHT_Y = 134

    def __init__(self, pdf: pdfplumber.PDF):
        self.pdf = pdf

    def parse_question_paper(self):
        self.chars = self.read_texts()
        questions = []
        question_starts = self.find_question_starts()
        for i, question_start in enumerate(question_starts):
            if i == len(question_starts) - 1:
                question_end = len(self.chars)
            else:
                question_end = question_starts[i + 1]
            question = self.parse_question(question_start, question_end, i + 1)
            questions.append(question)
        return questions

    def read_texts(self):
        chars = []
        for i, page in enumerate(self.pdf.pages[1:]):
            if re.search(r"BLANK PAGE", page.extract_text()):
                continue
            page_chars = page.chars
            page_chars = list(
                filter(
                    lambda x: x["y0"]
                    > (
                        self.IGNORE_PAGE_FOOTER_Y
                        if (i != len(self.pdf.pages) - 2)
                        else self.LAST_PAGE_COPYRIGHT_Y
                    )
                    and x["y0"] != self.PAGE_NUMBER_Y,
                    page_chars,
                )
            )
            chars.extend(
                [(char["x0"], char["y0"], char["text"]) for char in page_chars]
            )
        return chars

    def find_question_starts(self):
        question_starts = []
        current_number = 1
        for i, (x, _, _) in enumerate(self.chars):
            if abs(x - self.QUESTION_START_X) <= 2:
                text = "".join(char[2] for char in self.chars[i : i + 3])
                if re.match(
                    f"{current_number}",
                    text,
                ):
                    question_starts.append(i)
                    current_number += 1

        return question_starts

    def parse_question(self, start_index: int, end_index: int, number: int):
        subquestion_starts = self.find_subquestion_starts(start_index, end_index)
        if subquestion_starts:
            subquestions = []
            question_text = "".join(
                char[2] for char in self.chars[start_index : subquestion_starts[0]]
            )
            for i, subquestion_start in enumerate(subquestion_starts):
                if i == len(subquestion_starts) - 1:
                    subquestion_end = end_index
                else:
                    subquestion_end = subquestion_starts[i + 1]
                subquestions.append(
                    self.parse_subquestion(
                        subquestion_start,
                        subquestion_end,
                        chr(ord("a") + i),
                    )
                )
        else:
            subquestions = None
            question_text = "".join(
                char[2] for char in self.chars[start_index:end_index]
            )
        return Question(
            number=number,
            text=question_text,
            subquestions=subquestions,
        )

    def parse_subquestion(self, start_index: int, end_index: int, number: str):
        subsubquestion_starts = self.find_subsubquestion_starts(start_index, end_index)
        if subsubquestion_starts:
            subsubquestions = []
            subquestion_text = "".join(
                char[2] for char in self.chars[start_index : subsubquestion_starts[0]]
            )
            for i, subsubquestion_start in enumerate(subsubquestion_starts):
                if i == len(subsubquestion_starts) - 1:
                    subsubquestion_end = end_index
                else:
                    subsubquestion_end = subsubquestion_starts[i + 1]
                subsubquestions.append(
                    self.parse_subsubquestion(
                        subsubquestion_start,
                        subsubquestion_end,
                        self.SUBSUBQUESTION_STARTS[i][0],
                    )
                )
        else:
            subsubquestions = None
            subquestion_text = "".join(
                char[2] for char in self.chars[start_index:end_index]
            )
        return SubQuestion(
            number=number,
            text=subquestion_text,
            subsubquestions=subsubquestions,
        )

    def parse_subsubquestion(self, start_index: int, end_index: int, number: str):
        subsubquestion_text = "".join(
            char[2] for char in self.chars[start_index:end_index]
        )
        return SubSubQuestion(number=number, text=subsubquestion_text)

    def find_subquestion_starts(self, start_index: int, end_index: int):
        subquestion_starts = []
        current_question_alpha = "a"
        for i in range(start_index, end_index):
            x, _, _ = self.chars[i]
            if abs(x - self.SUBQUESTION_START_X) <= 2:
                text = "".join(char[2] for char in self.chars[i : i + 5])
                if re.match(r"\(" + current_question_alpha + r"\)", text):
                    current_question_alpha = chr(ord(current_question_alpha) + 1)
                    subquestion_starts.append(i)
        return subquestion_starts

    def find_subsubquestion_starts(self, start_index: int, end_index: int):
        subsubquestion_starts = []
        current_subsubquestion_roman_index = 0
        for i in range(start_index, end_index):
            x, _, _ = self.chars[i]
            if (
                abs(
                    x
                    - self.SUBSUBQUESTION_STARTS[current_subsubquestion_roman_index][1]
                )
                <= 2
            ):
                text = "".join(char[2] for char in self.chars[i : i + 5])
                if re.match(
                    r"\("
                    + self.SUBSUBQUESTION_STARTS[current_subsubquestion_roman_index][0]
                    + r"\)",
                    text,
                ):
                    current_subsubquestion_roman_index += 1
                    subsubquestion_starts.append(i)

        return subsubquestion_starts


def format_question_hierarchy(questions):
    output = ""
    for q in questions:
        output += f"\n{q.number}:\n"
        if q.subquestions:
            for sub_q in q.subquestions:
                text = sub_q.text.strip()
                output += f"\n    {text}\n"
                if sub_q.subsubquestions:
                    for subsub_q in sub_q.subsubquestions:
                        text = subsub_q.text.strip()
                        output += f"\n        {text}\n"
        output += "\n" + "-" * 80 + "\n"
    return output.strip()


class MarkSchemeParser:
    def __init__(self, pdf: pdfplumber.PDF):
        self.pdf = pdf

    def extract_lines(self):
        lines = []
        for page in self.pdf.pages[5:]:
            page_lines = [(rect["x0"], rect["y0"]) for rect in page.rects]
            lines.append(page_lines)
        return lines


def main():
    qp_path = "papers/igcse-history-0470/0470_w24_qp_41.pdf"
    ms_path = "papers/igcse-biology-0610/0610_w22_ms_42.pdf"

    with open("output.txt", "w", encoding="utf-8") as f:
        with pdfplumber.open(qp_path) as qp_pdf:
            qp_parser = QuestionPaperParser(qp_pdf)
            qp_questions = qp_parser.parse_question_paper()
            formatted_output = format_question_hierarchy(qp_questions)
            f.write(formatted_output)
        # with pdfplumber.open(ms_path) as ms_pdf:
        #     ms_parser = MarkSchemeParser(ms_pdf)
        #     lines = ms_parser.extract_lines()
        #     f.write(pprint.pformat(lines, width=80))


if __name__ == "__main__":
    main()
