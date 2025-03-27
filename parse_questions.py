import re
from dataclasses import dataclass
import pdfplumber
import os
from typing import List, Optional, Tuple
from itertools import combinations


@dataclass(frozen=True)
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
        self, number: str, text: str, marks: int, answer: Optional[MarkScheme] = None
    ):
        self.number = number
        self.text = text
        self.marks = marks
        self.answer = answer

    def __str__(self):
        return f"Q{self.number}: {self.text} [{self.marks}]"


@dataclass
class SubQuestion:

    def __init__(
        self,
        number: str,
        text: str,
        subsubquestions: Optional[List[SubSubQuestion]],
        marks: int,
        answer: Optional[MarkScheme] = None,
    ):
        self.number = number
        self.text = text
        self.subsubquestions = subsubquestions
        self.answer = answer
        self.marks = marks

    def __str__(self):
        return f"Q{self.number}: {self.text} [{self.marks}]"


@dataclass
class Question:
    def __init__(
        self,
        number: int,
        text: str,
        subquestions: List[SubQuestion],
        marks: int,
        answer: Optional[MarkScheme],
    ):
        self.number = number
        self.text = text
        self.subquestions = subquestions
        self.marks = marks
        self.answer = answer

    def __str__(self):
        return f"Q{self.number}: {self.text} [{self.marks}]"


def clean_text(text: str) -> str:
    text = re.sub(r"\[Turn over", "", text)

    # Clean empty tags
    text = re.sub(r"<b>\s*</b>", "", text)
    text = re.sub(r"<i>\s*</i>", "", text)

    # Normalize spacing around tags
    text = re.sub(r"\s*<b>\s*([^<>]+?)\s*</b>\s*", r"<b>\1</b>", text)
    text = re.sub(r"\s*<i>\s*([^<>]+?)\s*</i>\s*", r"<i>\1</i>", text)

    # remove ...
    text = re.sub(r"\.\.+", "", text)

    text = re.sub(r"<b>\d+</b>\d+/\d+/.+/.+/.+© UCLES 20\d+", "", text)
    return text


def extract_md_from_pdf(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[1:]:
            chars = page.chars
            page_text = ""
            prev_is_bold = False
            prev_is_italic = False
            for char in chars:
                if not char["text"]:
                    continue
                font_name = char.get("fontname", "").lower()
                is_bold = "bold" in font_name
                is_italic = "italic" in font_name
                # format to markdown, concat with previous text
                if is_bold and not prev_is_bold:
                    page_text += "<b>"
                elif prev_is_bold and not is_bold:
                    page_text += "</b>"
                if is_italic and not prev_is_italic:
                    page_text += "<i>"
                elif prev_is_italic and not is_italic:
                    page_text += "</i>"
                page_text += char["text"]
                prev_is_bold = is_bold
                prev_is_italic = is_italic
            if prev_is_bold:
                page_text += "</b>"
            if prev_is_italic:
                page_text += "</i>"

            page_text = clean_text(page_text)
            page_text += "\n"
            if "BLANK PAGE" in page_text:
                continue
            text += page_text
    return text


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text


class ParserError(Exception):
    pass


class QuestionPaperParser:
    QUESTION_START = r"(?:(?<=<b>)(\d+)(?=</b>)|<b>(\d+)</b>)"
    SUBQUESTION_START = r"(?:(?<=<b>)\(([A-Za-z])\)(?=</b>)|<b>\(([A-Za-z])\)</b>)"
    SUBSUBQUESTION_START = r"(?:(?<=<b>)\((i{1,3}|iv|v|vi{1,3}|x)\)(?=</b>)|<b>\((i{1,3}|iv|v|vi{1,3}|x)\)</b>)"
    MARK = r"\s*\[(\d+)\]\s*"
    TOTAL_MARKS = r"\s*\[Total: (\d+)\]\s*"

    def __init__(self, text: str):
        self.text = text
        self.cursor = 0

    def find_question_starts(self) -> List[int]:
        numbers = [
            (m.start(), int(m.group(1) or m.group(2)))
            for m in re.finditer(self.QUESTION_START, self.text)
        ]

        result = []
        for length in range(1, len(numbers) + 1):
            for combo in combinations(range(len(numbers)), length):
                # Get the selected number pairs
                selected = [numbers[i] for i in combo]
                # Check if the numbers form a sequence starting from 1
                nums = [n[1] for n in selected]
                if nums == list(range(1, len(nums) + 1)):
                    # If valid, add the list of positions to result
                    result.append([n[0] for n in selected])

        return result

    def find_subquestion_starts(self, start: int, end: int) -> List[int]:
        return [
            m.start() for m in re.finditer(self.SUBQUESTION_START, self.text[start:end])
        ]

    def find_subsubquestion_starts(self, start: int, end: int) -> List[int]:
        return [
            m.start()
            for m in re.finditer(self.SUBSUBQUESTION_START, self.text[start:end])
        ]

    def parse(self) -> List[Question]:
        question_starts = self.find_question_starts()
        for starts in question_starts:
            try:
                questions = self.parse_questions(starts)
            except ParserError as e:
                pass
        return questions

    def parse_questions(self, starts: List[int]):
        questions = []
        for i, start in enumerate(starts):
            self.cursor = start
            question = self.parse_question(
                starts[i + 1] if i + 1 < len(starts) else len(self.text)
            )
            questions.append(question)
        return questions

    def parse_question(self, end: int) -> Question:
        starts = self.find_subquestion_starts(self.cursor, end)
        number = self.parse_question_number()
        if not starts.empty():
            text = self.text[self.cursor : starts[0]]
            self.cursor = starts[0]
            subquestions = self.parse_subquestions(starts)
            marks = self.parse_total_marks()
        else:
            text = self.text[self.cursor : end]
            subquestions = []
            self.cursor = end
            marks = self.parse_marks()
        return Question(number, text, subquestions, marks, None)

    def text_until(self, patterns: List[str]) -> str:
        # Combine patterns with OR operator
        combined_pattern = "|".join(f"(?:{p})" for p in patterns)
        match = re.search(combined_pattern, self.text[self.cursor :], re.VERBOSE)
        if not match:
            raise ParserError(
                "Invalid text", self.text[self.cursor : self.cursor + 100]
            )
        text = self.text[self.cursor : match.start()]
        self.cursor += match.start()
        return text


def main():
    qp_path = "papers/igcse-biology-0610/0610_w22_qp_42.pdf"
    ms_path = "papers/igcse-biology-0610/0610_w22_ms_42.pdf"

    qp_text = extract_md_from_pdf(qp_path)
    ms_text = extract_text_from_pdf(ms_path)

    with open("output.md", "w", encoding="utf-8") as f:
        f.write("Question Paper:\n")
        f.write(qp_text)
        f.write("\nMark Scheme:\n")
        f.write(ms_text)
        f.write("\n")

    qp_parser = QuestionPaperParser(qp_text)
    questions = qp_parser.parse_questions()
    for question in questions:
        print(question)


if __name__ == "__main__":
    main()

    # def parse_questions(self) -> List[Question]:
    #     questions = []
    #     while self.cursor < len(self.text):
    #         question = self.parse_question()
    #         questions.append(question)
    #     return questions

    # def parse_question(self) -> Question:
    #     number = self.parse_question_number()
    #     text = self.parse_question_text()
    #     subquestions = self.parse_subquestions()
    #     marks = self.parse_total_marks()
    #     return Question(number, text, subquestions, marks)

    # def parse_question_number(self) -> int:
    #     match = re.match(self.QUESTION_START, self.text[self.cursor :])
    #     if not match:
    #         raise ParserError(
    #             "Invalid question number", self.text[self.cursor : self.cursor + 100]
    #         )
    #     self.cursor += match.end()
    #     return int(match.group(2))

    # def parse_question_text(self) -> str:
    #     return self.text_until(
    #         [self.SUBQUESTION_START, self.TOTAL_MARKS, self.MARK, self.QUESTION_START]
    #     )

    # def parse_subquestions(self) -> List[SubQuestion]:
    #     subquestions = []
    #     while self.cursor < len(self.text) and re.match(
    #         self.SUBQUESTION_START, self.text[self.cursor :]
    #     ):
    #         subquestion = self.parse_subquestion()
    #         explaination_between = self.text_until(
    #             [
    #                 self.SUBQUESTION_START,
    #                 self.TOTAL_MARKS,
    #                 self.QUESTION_START,
    #             ]
    #         )
    #         print(explaination_between)
    #         subquestions.append(subquestion)
    #     return subquestions

    # def parse_subquestion(self) -> SubQuestion:
    #     number = self.parse_subquestion_number()
    #     text = self.parse_subquestion_text()
    #     if re.match(self.SUBSUBQUESTION_START, self.text[self.cursor :]):
    #         subsubquestions = self.parse_subsubquestions()
    #         marks = sum(subsubquestion.marks for subsubquestion in subsubquestions)
    #     else:
    #         subsubquestions = None
    #         marks = self.parse_marks()
    #     return SubQuestion(number, text, subsubquestions, marks)

    # def parse_subquestion_number(self) -> str:
    #     match = re.match(self.SUBQUESTION_START, self.text[self.cursor :])
    #     if not match:
    #         raise ParserError(
    #             "Invalid subquestion number", self.text[self.cursor : self.cursor + 100]
    #         )
    #     self.cursor += match.end()
    #     return match.group(2)

    # def parse_subquestion_text(self) -> str:
    #     return self.text_until([self.MARK, self.SUBSUBQUESTION_START])

    # def parse_subsubquestions(self) -> List[SubSubQuestion]:
    #     subsubquestions = []
    #     while self.cursor < len(self.text) and re.match(
    #         self.SUBSUBQUESTION_START, self.text[self.cursor :]
    #     ):
    #         subsubquestion = self.parse_subsubquestion()
    #         subsubquestions.append(subsubquestion)
    #     return subsubquestions

    # def parse_subsubquestion(self) -> SubSubQuestion:
    #     number = self.parse_subsubquestion_number()
    #     text = self.parse_subsubquestion_text()
    #     marks = self.parse_marks()
    #     return SubSubQuestion(number, text, marks)

    # def parse_subsubquestion_number(self) -> str:
    #     match = re.match(self.SUBSUBQUESTION_START, self.text[self.cursor :])
    #     if not match:
    #         raise ParserError(
    #             "Invalid subsubquestion number",
    #             self.text[self.cursor : self.cursor + 100],
    #         )
    #     self.cursor += match.end()
    #     return match.group(2)

    # def parse_subsubquestion_text(self) -> str:
    #     return self.text_until([self.MARK])

    # def parse_marks(self) -> int:
    #     match = re.match(self.MARK, self.text[self.cursor :])
    #     if not match:
    #         raise ParserError(
    #             "Invalid marks", self.text[self.cursor : self.cursor + 100]
    #         )
    #     self.cursor += match.end()
    #     return int(match.group(1))

    # def parse_total_marks(self) -> int:
    #     match = re.match(self.TOTAL_MARKS, self.text[self.cursor :])
    #     if not match:
    #         raise ParserError(
    #             "Invalid total marks", self.text[self.cursor : self.cursor + 100]
    #         )
    #     self.cursor += match.end()
    #     return int(match.group(1))
