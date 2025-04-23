from parser.sq_parser import QuestionPaperParser
from parser.sq_ms_parser import SQMSParser
from parser.mcq_parser import MCQParser
from parser.mcq_ms_parser import MCQMSParser
from parser.syllabus_parser import SyllabusParser
from classify.classify_llm import LLMClassifier

from parser.models.question import MultipleChoiceQuestion
from parser.models.question import Question, SubQuestion, SubSubQuestion
from parser.models.syllabus import Syllabus

import pdfplumber
from typing import List, Optional
import os
import re
from dotenv import load_dotenv

load_dotenv()

CONFIGS = {
    "igcse-biology-0610": {
        "syllabus_path": "papers/595426-2023-2025-syllabus.pdf",
        "syllabus_page_range": (12, 46),
        "sq_prefix": ["3", "4", "5", "6"],
    },
}


def parse(
    classifier: LLMClassifier,
    questions: List[Question],
    question_paper: str,
    markscheme: str,
    issq: bool,
) -> List[Question] | List[MultipleChoiceQuestion]:
    if issq:
        with pdfplumber.open(question_paper) as qppdf:
            sq_parser = QuestionPaperParser(
                qppdf, image_prefix=os.path.basename(question_paper)[:-4]
            )
            questions = sq_parser.parse_question_paper()
        sqms_parser = SQMSParser(markscheme, questions)
        questions = sqms_parser.parse_ms()
        questions = classifier.classify_all(questions)
        return questions
    else:
        with pdfplumber.open(question_paper) as qppdf:
            mcq_parser = MCQParser(
                qppdf, image_prefix=os.path.basename(question_paper)[:-4]
            )
            questions = mcq_parser.parse_question_paper()
        mcqms_parser = MCQMSParser(markscheme, questions)
        mcqms_parser.parse_no_error()
        questions = classifier.classify_all(questions)
        return questions

print(config for config in CONFIGS.keys())
path = input("Select a config: ")
config = CONFIGS[path]
syllabus_path = config["syllabus_path"]
syllabus_page_range = config["syllabus_page_range"]
sq_prefix = config["sq_prefix"]


result = re.match(
    r"\d{4}_\w\d{2}_\w+_(\d)\d\.pdf", os.path.basename(question_paper)
)
if result.group(1):
    