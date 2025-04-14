from parser.models.question import (
    Question,
    SubQuestion,
    SubSubQuestion,
    MultipleChoiceQuestion,
)
from parser.models.syllabus import Syllabus
from typing import Any, Dict, List, Optional
from transformers import AutoTokenizer, AutoModel
import torch
from torch.nn.functional import cosine_similarity

# 加载 SciBERT 模型
tokenizer = AutoTokenizer.from_pretrained("allenai/scibert_scivocab_uncased")
model = AutoModel.from_pretrained("allenai/scibert_scivocab_uncased")


class Classifier:
    def __init__(
        self,
        syllabuses: List[Syllabus],
        questions: List[Question | MultipleChoiceQuestion],
    ):
        self.syllabuses = syllabuses
        self.questions = questions

    @staticmethod
    def get_sentence_embedding(sentence: str):
        inputs = tokenizer(
            sentence.lower(), return_tensors="pt", truncation=True, padding=True
        )
        with torch.no_grad():
            outputs = model(**inputs)
        cls_embedding = outputs.last_hidden_state[:, 0, :]  # shape: (1, hidden_size)
        return cls_embedding.squeeze()

    @staticmethod
    def get_similarity(embedding1, embedding2):
        return cosine_similarity(embedding1, embedding2, dim=0).item()

    def classify_all(self) -> None:
        for question in self.questions:
            self.classify(question)

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
        print(question.answer)
        # Assign the best syllabus to the smallest question object recursively
        question.syllabus = self.get_best_syllabus(
            question.text + " " + question.answer
        )

    def get_best_syllabus(self, question_sentence: str) -> Syllabus:
        question_embedding = self.get_sentence_embedding(question_sentence)
        best_similarity = float("-inf")
        best_syllabus = None
        for syllabus in self.syllabuses:
            for point in syllabus.content:
                syllabus_embedding = self.get_sentence_embedding(point)
                similarity = self.get_similarity(question_embedding, syllabus_embedding)

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_syllabus = syllabus

        return best_syllabus


if __name__ == "__main__":
    from parser.sq_ms_parser import SQMSParser
    from parser.sq_parser import QuestionPaperParser
    from parser.syllabus_parser import SyllabusParser
    import pdfplumber

    with pdfplumber.open("papers/595426-2023-2025-syllabus.pdf") as syllabus_pdf:
        syllabus_parser = SyllabusParser(syllabus_pdf, pages=(12, 46))
        syllabuses = syllabus_parser.parse_syllabus()
    with pdfplumber.open("papers/igcse-biology-0610/0610_w22_qp_42.pdf") as qppdf:
        sq_parser = QuestionPaperParser(qppdf, image_prefix="0610_w22_qp_42")
        questions = sq_parser.parse_question_paper()
    sqms_parser = SQMSParser("papers/igcse-biology-0610/0610_w22_ms_42.pdf", questions)
    questions = sqms_parser.parse_ms()
    classifier = Classifier(syllabuses, questions)
    classifier.classify_all()
    for question in questions:
        print(question)
        print(question.syllabus)
