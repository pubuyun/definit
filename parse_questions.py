import re
from dataclasses import dataclass
import pdfplumber
import os
from typing import List, Optional, Tuple
from itertools import combinations

import pprint

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

class ParserError(Exception):
    pass


class QuestionPaperParser:
    QUESTION_START_X = 49.6063
    SUBQUESTION_START_X = 72
    SUBSUBQUESTION_I_START_X = 96
    SUBSUBQUESTION_II_START_X = 93
    SUBSUBQUESTION_III_START_X = 90
    SUBSUBQUESTION_IV_START_X = 90
    SUBSUBQUESTION_V_START_X = 93
    IGNORE_PAGE_FOOTER_Y = 35
    PAGE_NUMBER_Y = 790.4778
    
    def __init__(self, pdf: pdfplumber.PDF):
        self.pdf = pdf
        
    def read_texts(self):
        chars = []
        for page in self.pdf.pages[1:]:
            page_chars = page.chars
            page_chars = list(filter(lambda x: x["y0"] > self.IGNORE_PAGE_FOOTER_Y and x["y0"] != self.PAGE_NUMBER_Y, page_chars))
            chars.extend(page_chars)
            
        return texts

            

    

    


def main():
    qp_path = "papers/igcse-biology-0610/0610_w22_qp_42.pdf"
    ms_path = "papers/igcse-biology-0610/0610_w22_ms_42.pdf"


    with open("output.py", "w", encoding="utf-8") as f:
        with pdfplumber.open(qp_path) as qp_pdf:
            qp_parser = QuestionPaperParser(qp_pdf)
            qp_texts = qp_parser.read_texts()
        f.write(pprint.pformat(qp_texts))

 
if __name__ == "__main__":
    main()
'''
  
def clean_text(text: str) -> str:
    text = re.sub(r"\[Turn over", "", text)
    # remove ...
    text = re.sub(r"\.\.+", "", text)
    # remove UCLES copyright
    text = re.sub(r\d+\d+/\d+/.+/.+/.+© UCLES 20\d+", "", text)

    # remove Permission  to  reproduce  items  where  third‑party...
    text = re.sub(
        r"Permission  to  reproduce  items  .*", "", text
    )
'''