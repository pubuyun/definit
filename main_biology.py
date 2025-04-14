from parser.sq_parser import QuestionPaperParser
from parser.sq_ms_parser import SQMSParser
from parser.mcq_parser import MCQParser
from parser.mcq_ms_parser import MCQMSParser
from parser.syllabus_parser import SyllabusParser
from classify.classify import Classifier

from parser.models.question import MultipleChoiceQuestion
from parser.models.question import Question, SubQuestion, SubSubQuestion
from parser.models.syllabus import Syllabus

import pdfplumber
from typing import List, Optional


def get_questions(
    syllabuses: List[Syllabus],
    question_paper_pdf: pdfplumber.pdf,
    mark_scheme_pdf: pdfplumber.pdf,
    is_mcq: bool,
) -> List[Question]:
    if is_mcq:
        mcq_parser = MCQParser(question_paper_pdf)
        questions = mcq_parser.parse_question_paper()
        mcqms_parser = MCQMSParser(mark_scheme_pdf, questions)
        questions = mcqms_parser.parse_ms()
    else:
        sq_parser = QuestionPaperParser(question_paper_pdf)
        questions = sq_parser.parse_question_paper()
        sqms_parser = SQMSParser(mark_scheme_pdf, questions)
        questions = sqms_parser.parse_ms()
    classifier = Classifier(syllabuses, questions)
    classifier.classify_all()
    return questions
