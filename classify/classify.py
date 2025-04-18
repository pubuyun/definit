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
import pickle
import os
import numpy as np
from collections import Counter
from sentence_transformers import SentenceTransformer, util


class Classifier:

    def __init__(
        self,
        syllabuses: List[Syllabus],
        batch_size: int = 64,
        cache_path: str = "syllabus_embeddings.pkl",
        model_name: str = "allenai/scibert_scivocab_uncased",
    ):
        self.batch_size = batch_size
        self.cache_path = cache_path
        self.syllabus_objects = syllabuses

        print(f"Initializing SentenceTransformer with model: {model_name}")
        self.model = SentenceTransformer(model_name)

        # Try to load cache, otherwise process syllabuses
        if os.path.exists(cache_path) and self._try_load_cache():
            print(f"Loaded embeddings from cache: {cache_path}")
        else:
            print("Processing syllabus content...")
            self._preprocess_syllabuses(syllabuses)
            self._save_cache()

    def _preprocess_syllabuses(self, syllabuses: List[Syllabus]) -> None:
        # Create corpus and mapping
        self.corpus = []
        self.syllabus_mapping = []

        for idx, syllabus in enumerate(syllabuses):
            for point in syllabus.content:
                text = point.lower().strip()
                self.corpus.append(text)
                self.syllabus_mapping.append(idx)

        print(f"Encoding {len(self.corpus)} syllabus points")
        self.corpus_embeddings = self.model.encode(
            self.corpus,
            batch_size=self.batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
        )

    def _save_cache(self) -> None:
        cache_data = {
            "corpus": self.corpus,
            "corpus_embeddings": self.corpus_embeddings,
            "syllabus_mapping": self.syllabus_mapping,
        }
        with open(self.cache_path, "wb") as f:
            pickle.dump(cache_data, f)
        print(f"Embeddings cached to {self.cache_path}")

    def _try_load_cache(self) -> bool:
        try:
            with open(self.cache_path, "rb") as f:
                cache_data = pickle.load(f)
                self.corpus = cache_data["corpus"]
                self.corpus_embeddings = cache_data["corpus_embeddings"]
                self.syllabus_mapping = cache_data["syllabus_mapping"]
            return True
        except Exception as e:
            print(f"Cache load failed: {str(e)}")
            return False

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
        # Clean text: remove more than three connected dots and score markers
        question_sentence = re.sub(r"\.{3,}", "", question_sentence)
        question_sentence = re.sub(r"\[\d+\]", "", question_sentence)
        question_sentence = re.sub(r"\(\w{1,3}\)", "", question_sentence)

        # Get embedding for the question
        question_embedding = self.model.encode(question_sentence, convert_to_numpy=True)

        similarities = util.semantic_search(
            question_embedding,
            self.corpus_embeddings,
            top_k=10,
            score_function=util.cos_sim,
        )

        weighted_similarities = Counter()
        for hit in filter(lambda x: x["score"] > threshold, similarities[0]):
            syllabus_idx = self.syllabus_mapping[hit["corpus_id"]]
            weighted_similarities[syllabus_idx] += hit["score"]

        if not weighted_similarities:
            return Syllabus("0", "unknown")
        return self.syllabus_objects[weighted_similarities.most_common(1)[0][0]]


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
    classifier = Classifier(syllabuses, cache_path="biology_syllabus.pt")
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
