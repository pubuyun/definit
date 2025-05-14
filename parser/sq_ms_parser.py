from parser.ms_parser import Parser
from pdf2docx import Converter
from typing import List, Optional
import re
from parser.models.question import Question, SubQuestion, SubSubQuestion


class SQMSParser(Parser):
    def __init__(
        self,
        pdf_path: str,
        questions: List[Question],
        image_prefix: str = "example-",
    ):
        self.questions = questions
        super().__init__(pdf_path, image_prefix)

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
                image_path = ms["Image"]
                # Assign answer to the appropriate question/subquestion/subsubquestion
                self.assign_to_question(
                    answer,
                    marks,
                    question_number,
                    image_path,
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
        image_path: str | List[str],
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
            matching_question.ms_image = image_path
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
            matching_subquestion.ms_image = image_path
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
            matching_subquestion.ms_image = image_path

    def complete_answers(self):
        # Complete subsubquestion answers first
        for question in self.questions:
            if not question.subquestions:
                continue
            for subquestion in question.subquestions:
                # Update subquestion's answer and ms_image by concatenating subsubquestion data
                if subquestion.subsubquestions:
                    # Handle answers
                    if not subquestion.answer:
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

                    # Handle ms_images
                    if not subquestion.ms_image:
                        ms_images = [
                            ssq.ms_image
                            for ssq in subquestion.subsubquestions
                            if ssq.ms_image
                        ]
                        if ms_images:
                            subquestion.ms_image = ms_images

            # Update question's answer and ms_image by concatenating subquestion data
            if question.subquestions:
                # Handle answers
                if not question.answer:
                    answers = [
                        f"({sq.number}) {sq.answer}"
                        for sq in question.subquestions
                        if sq.answer
                    ]
                    if answers:
                        question.answer = "\n".join(answers)
                        question.marks = sum(
                            sq.marks
                            for sq in question.subquestions
                            if sq.marks is not None
                        )

                # Handle ms_images
                if not question.ms_image:
                    ms_images = []
                    for sq in question.subquestions:
                        if isinstance(sq.ms_image, list):
                            ms_images.extend(sq.ms_image)
                        elif sq.ms_image:
                            ms_images.append(sq.ms_image)
                    if ms_images:
                        question.ms_image = ms_images


if __name__ == "__main__":
    from sq_parser import QuestionPaperParser
    import pdfplumber

    qp_path = "papers/igcse-biology-0610/0610_m15_qp_32.pdf"
    ms_path = "papers/igcse-biology-0610/0610_m15_ms_32.pdf"

    def format_question_hierarchy(questions):
        output = ""
        for q in questions:
            output += f"{q.answer}\n"
            if q.subquestions:
                for sub_q in q.subquestions:
                    output += f"\n    {sub_q.answer.strip() if sub_q.answer else ''}\n"
                    if sub_q.subsubquestions:
                        for subsub_q in sub_q.subsubquestions:
                            output += f"\n        {subsub_q.answer.strip() if subsub_q.answer else ''}\n"
            output += "\n" + "-" * 80 + "\n"
        return output.strip()

    with pdfplumber.open(qp_path) as pdf:
        qp = QuestionPaperParser(pdf, image_prefix="0610_w22_qp_42")
        questions = qp.parse_question_paper()
    with pdfplumber.open(ms_path) as pdf:
        ms = SQMSParser(
            pdf_path=ms_path, questions=questions, image_prefix="0610_w22_ms_42"
        )
    questions = ms.parse_ms()
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(format_question_hierarchy(questions))
