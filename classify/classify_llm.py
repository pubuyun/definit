from parser.models.question import (
    Question,
    SubQuestion,
    SubSubQuestion,
    MultipleChoiceQuestion,
)
from parser.models.syllabus import Syllabus

from typing import List, Optional
import re
import tqdm



class LLMClassifier:

    def __init__(
        self,
        syllabuses: List[Syllabus],
        batch_size: int = 64,
        cache_path: str = "syllabus_embeddings.pkl",
        model_name: str = "allenai/scibert_scivocab_uncased",
    ):
        pass

    def classify_all(
        self, questions: List[Question | MultipleChoiceQuestion]
    ) -> List[Question | MultipleChoiceQuestion]:
        for question in tqdm.tqdm(questions, desc="Classifying questions"):
            self.classify(question)
        return questions

    def classify(
        self, question: MultipleChoiceQuestion | Question | SubQuestion | SubSubQuestion
    ) -> None:
        if isinstance(question, MultipleChoiceQuestion):
            question.syllabus = self.get_best_syllabus(question.text)
            return
        elif isinstance(question, SubQuestion):
            if question.subsubquestions:
                for subsubquestion in question.subsubquestions:
                    self.classify(subsubquestion)
        elif isinstance(question, Question):
            if question.subquestions:
                for subquestion in question.subquestions:
                    self.classify(subquestion)

        # Combine question text and answer for better matching
        question_text = (
            question.text + " " + (question.answer if question.answer else "")
        )
        question.syllabus = self.get_best_syllabus(question_text)

    def get_best_syllabus(self, question_sentence: str, threshold=0.3) -> Syllabus:
        pass


if __name__ == "__main__":
    from parser.sq_ms_parser import SQMSParser
    from parser.sq_parser import QuestionPaperParser
    from parser.syllabus_parser import SyllabusParser
    import pdfplumber
    import pprint

    with pdfplumber.open("papers/595426-2023-2025-syllabus.pdf") as syllabus_pdf:
        syllabus_parser = SyllabusParser(syllabus_pdf, pages=(12, 46))
        syllabuses = syllabus_parser.parse_syllabus()
    with pdfplumber.open("papers/igcse-biology-0610/0610_w22_qp_42.pdf") as qppdf:
        sq_parser = QuestionPaperParser(qppdf, image_prefix="0610_w22_qp_42")
        questions = sq_parser.parse_question_paper()
    sqms_parser = SQMSParser("papers/igcse-biology-0610/0610_w22_ms_42.pdf", questions)
    questions = sqms_parser.parse_ms()
    classifier = LLMClassifier(syllabuses, cache_path="biology_syllabus.pt")
    questions = classifier.classify_all(questions)

    def format_question_hierarchy(questions):
        output = ""
        for q in questions:
            output += (
                f"{q.text}\n{q.syllabus.title if hasattr(q, "syllabus") else ""}\n "
            )
            if q.subquestions:
                for sub_q in q.subquestions:
                    text = sub_q.text.strip()
                    output += f"\n    {text}\n{sub_q.syllabus.title if hasattr(sub_q, "syllabus") else ""}"
                    if sub_q.subsubquestions:
                        for subsub_q in sub_q.subsubquestions:
                            text = subsub_q.text.strip()
                            subsub_q: SubSubQuestion
                            output += f"\n        {text}\n{subsub_q.syllabus.title if hasattr(subsub_q, "syllabus") else ""}\n"
            output += "\n" + "-" * 80 + "\n"
        return output.strip()

    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(format_question_hierarchy(questions))
