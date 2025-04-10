from ms_parser import Parser
from pdf2docx import Converter
from typing import List, Optional
import re
from models.question import Question, SubQuestion, SubSubQuestion


class SQMSParser(Parser):
    def __init__(self, pdf_path: str, questions: List[Question]):
        super().__init__(pdf_path)
        self.questions = questions

    def parse_ms(self):
        for ms in self.tables:
            pattern = r"(\d+)(?:\(([a-z])\))?(?:\(([ix]+)\))?"
            # example: 1(a)(i)
            matches = re.match(pattern, ms["Question"])
            if matches:
                question_number = int(matches.group(1))
                subquestion_number = matches.group(2) if matches.group(2) else None
                subsubquestion_number = matches.group(3) if matches.group(3) else None
                answer = ms["Answer"]
                marks = int(ms["Marks"]) if ms["Marks"] else 0

                # Assign answer to the appropriate question/subquestion/subsubquestion
                self.assign_to_question(
                    answer,
                    marks,
                    question_number,
                    subquestion_number,
                    subsubquestion_number,
                )
            else:
                print(f"Failed to match question format: {ms['Question']}")
        self.complete_answers()
        return self.questions

    def assign_to_question(
        self,
        answer: str,
        marks: int,
        question_number: int,
        subquestion_number: Optional[str] = None,
        subsubquestion_number: Optional[str] = None,
    ):
        # Find matching question
        matching_question = next(
            (q for q in self.questions if q.number == question_number), None
        )
        if not matching_question:
            return

        # If no subquestion, assign directly to question
        if subquestion_number is None:
            matching_question.answer = answer
            matching_question.marks = marks
            return

        # Find matching subquestion
        matching_subquestion = next(
            (
                sq
                for sq in matching_question.subquestions
                if sq.number == subquestion_number
            ),
            None,
        )
        if not matching_subquestion:
            return

        # If no subsubquestion, assign to subquestion
        if subsubquestion_number is None:
            matching_subquestion.answer = answer
            matching_subquestion.marks = marks
            return

        # Find and assign to matching subsubquestion
        matching_subsubquestion = next(
            (
                ssq
                for ssq in matching_subquestion.subsubquestions
                if ssq.number == subsubquestion_number
            ),
            None,
        )
        if matching_subsubquestion:
            matching_subsubquestion.answer = answer
            matching_subsubquestion.marks = marks

    def complete_answers(self):
        # Complete subsubquestion answers first
        for question in self.questions:
            for subquestion in question.subquestions:
                # Update subquestion's answer by concatenating subsubquestion answers
                if not subquestion.answer and subquestion.subsubquestions:
                    answers = [
                        f"({ssq.number}) {ssq.answer}"
                        for ssq in subquestion.subsubquestions
                        if ssq.answer
                    ]
                    if answers:
                        subquestion.answer = "\n".join(answers)
                        subquestion.marks = sum(
                            ssq.marks
                            for ssq in subquestion.subsubquestions
                            if ssq.marks is not None
                        )

            # Update question's answer by concatenating subquestion answers
            if not question.answer and question.subquestions:
                answers = [
                    f"({sq.number}) {sq.answer}"
                    for sq in question.subquestions
                    if sq.answer
                ]
                if answers:
                    question.answer = "\n".join(answers)
                    question.marks = sum(
                        sq.marks for sq in question.subquestions if sq.marks is not None
                    )


if __name__ == "__main__":
    from sq_parser import QuestionPaperParser
    import pdfplumber

    qp_path = "papers/igcse-biology-0610/0610_w22_qp_42.pdf"
    ms_path = "papers/igcse-biology-0610/0610_w22_ms_42.pdf"
    with pdfplumber.open(qp_path) as pdf:
        qp = QuestionPaperParser(pdf)
        questions = qp.parse_question_paper()
    with pdfplumber.open(ms_path) as pdf:
        ms = SQMSParser(pdf_path=ms_path, questions=questions)
    questions = ms.parse_ms()
    for question in questions:
        print(question.answer)
