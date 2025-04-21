from parser.sq_parser import QuestionPaperParser
from parser.sq_ms_parser import SQMSParser
from parser.mcq_parser import MCQParser
from parser.mcq_ms_parser import MCQMSParser
from parser.syllabus_parser import SyllabusParser
from classify.classify_bert import Classifier

from parser.models.question import MultipleChoiceQuestion
from parser.models.question import Question, SubQuestion, SubSubQuestion
from parser.models.syllabus import Syllabus

import pdfplumber
from typing import List, Optional
import os


def get_questions(
    classifier: Classifier,
    qp_pdf: str,
    ms_pdf: str,
    is_mcq: bool,
) -> List[Question]:
    if is_mcq:
        with pdfplumber.open(qp_pdf) as qppdf:
            mcq_parser = MCQParser(
                qppdf, image_prefix=os.path.splitext(os.path.basename(qp_pdf))[0]
            )
            questions = mcq_parser.parse_question_paper()
        mcqms_parser = MCQMSParser(ms_pdf, questions)
        if mcqms_parser.parse_no_error():
            questions = mcqms_parser.mcqs
        else:
            print(f"Parsing error in {ms_pdf}.")
    else:
        with pdfplumber.open(qp_pdf) as qppdf:
            sq_parser = QuestionPaperParser(
                qppdf, image_prefix=os.path.splitext(os.path.basename(qp_pdf))[0]
            )
            questions = sq_parser.parse_question_paper()
        sqms_parser = SQMSParser(ms_pdf, questions)
        questions = sqms_parser.parse_ms()
    classifier.classify_all()
    return classifier.questions
