from parser.models.question import (
    Question,
    SubQuestion,
    SubSubQuestion,
    MultipleChoiceQuestion,
)
from parser.models.syllabus import Syllabus
from typing import Any, Dict, List, Optional, Tuple
import re
import torch
import tqdm
import hashlib
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np

# Check if GPU is available for TensorFlow
physical_devices = tf.config.list_physical_devices("GPU")
if physical_devices:
    tf.config.experimental.set_memory_growth(physical_devices[0], True)
    print("TensorFlow using GPU")
else:
    print("TensorFlow using CPU")

# Load Universal Sentence Encoder
print("Loading Universal Sentence Encoder...")
use_model = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
print("Model loaded")


class Classifier:
    def __init__(
        self,
        syllabuses: List[Syllabus],
        batch_size: int = 64,
        cache_path: str = "syllabus_embeddings.pt",
    ):
        self.batch_size = batch_size
        self.cache_path = cache_path
        current_hash = self._compute_syllabus_hash(syllabuses)
        if self._try_load_cache(syllabuses, current_hash):
            print("Loaded embeddings from cache")
        else:
            print("Generating new embeddings...")
            self.syllabus_embeddings, self.syllabus_mapping = (
                self._preprocess_syllabuses(syllabuses)
            )
            self._save_cache(current_hash)
        self.syllabus_objects = syllabuses

    def _compute_syllabus_hash(self, syllabuses: List[Syllabus]) -> str:
        hash_str = ""
        for syllabus in syllabuses:
            for point in syllabus.content:
                hash_str += point.lower().strip()
        return hashlib.md5(hash_str.encode()).hexdigest()

    def _preprocess_syllabuses(
        self, syllabuses: List[Syllabus]
    ) -> Tuple[torch.Tensor, List[int]]:
        all_points = []
        syllabus_indices = []
        for idx, syllabus in enumerate(syllabuses):
            for point in syllabus.content:
                all_points.append(point.lower().strip())
                syllabus_indices.append(idx)

        # Process in batches to avoid memory issues
        embeddings_list = []
        for i in tqdm.tqdm(
            range(0, len(all_points), self.batch_size), desc="Calculating embeddings"
        ):
            batch = all_points[i : i + self.batch_size]
            batch_embeddings = self.get_sentence_embeddings(batch)
            embeddings_list.extend(batch_embeddings)

        # Convert numpy embeddings to torch tensor
        embeddings_tensor = torch.tensor(np.array(embeddings_list), dtype=torch.float32)
        return embeddings_tensor, syllabus_indices

    def _save_cache(self, current_hash: str) -> None:
        cache_data = {
            "hash": current_hash,
            "embeddings": self.syllabus_embeddings,
            "syllabus_indices": self.syllabus_mapping,
        }
        torch.save(cache_data, self.cache_path)
        print(f"Embeddings cached to {self.cache_path}")

    def _try_load_cache(self, syllabuses: List[Syllabus], current_hash: str) -> bool:
        try:
            cache_data = torch.load(self.cache_path, map_location="cpu")
            if cache_data["hash"] != current_hash:
                print("Cache invalid: syllabus content changed")
                return False
            self.syllabus_embeddings = cache_data["embeddings"]
            self.syllabus_mapping = cache_data["syllabus_indices"]
            return True
        except Exception as e:
            print(f"Cache load failed: {str(e)}")
            return False

    @staticmethod
    def get_sentence_embeddings(sentences: List[str]) -> List[np.ndarray]:
        """Get embeddings for a batch of sentences using Universal Sentence Encoder"""
        # Clean and process sentences
        processed_sentences = []
        for sentence in sentences:
            # Remove multiple dots, scores, etc.
            clean_sentence = re.sub(r"\.{3,}", "", sentence)
            clean_sentence = re.sub(r"\[\d+\]", "", clean_sentence)

            # If sentence is too short, add padding
            if len(clean_sentence) < 3:
                clean_sentence = clean_sentence + " [padding]"

            processed_sentences.append(clean_sentence)

        # Generate embeddings using USE
        embeddings = use_model(processed_sentences).numpy()
        return list(embeddings)

    @staticmethod
    def get_sentence_embedding(sentence: str) -> np.ndarray:
        """Get embedding for a single sentence"""
        return Classifier.get_sentence_embeddings([sentence])[0]

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
        question.syllabus = self.get_best_syllabus(
            question.text + " " + question.answer if question.answer else ""
        )

    def get_best_syllabus(self, question_sentence: str) -> Syllabus:
        if not question_sentence:
            return Syllabus("0", "Unknown")

        # Clean question sentence
        question_sentence = re.sub(r"\.{3,}", "", question_sentence)
        question_sentence = re.sub(r"\[\d+\]", "", question_sentence)

        # Get question embedding using USE
        question_embedding = self.get_sentence_embedding(question_sentence)
        question_tensor = torch.tensor(question_embedding, dtype=torch.float32)

        # Calculate cosine similarity with all syllabus points
        similarities = torch.nn.functional.cosine_similarity(
            question_tensor.unsqueeze(0),
            self.syllabus_embeddings,
            dim=1,
        )
        print(question_sentence, similarities)

        # Get top 5 most similar points
        max_indices = torch.topk(similarities, 5).indices

        # Map to syllabus indices and find most common
        mapped_indices = torch.tensor([self.syllabus_mapping[i] for i in max_indices])
        syllabus_idx = torch.bincount(mapped_indices).argmax().item()

        return self.syllabus_objects[syllabus_idx]


if __name__ == "__main__":
    from parser.sq_ms_parser import SQMSParser
    from parser.sq_parser import QuestionPaperParser
    from parser.syllabus_parser import SyllabusParser
    import pdfplumber
    import pprint

    def format_question_hierarchy(questions):
        output = ""
        for q in questions:
            output += (
                f"{q.text}\n{q.syllabus.title if hasattr(q, 'syllabus') else ''}\n "
            )
            if q.subquestions:
                for sub_q in q.subquestions:
                    text = sub_q.text.strip()
                    output += f"\n    {text}\n{sub_q.syllabus.title if hasattr(sub_q, 'syllabus') else ''}"
                    if sub_q.subsubquestions:
                        for subsub_q in sub_q.subsubquestions:
                            text = subsub_q.text.strip()
                            subsub_q: SubSubQuestion
                            output += f"\n        {text}\n{subsub_q.syllabus.title if hasattr(subsub_q, 'syllabus') else ''}\n"
            output += "\n" + "-" * 80 + "\n"
        return output.strip()

    with pdfplumber.open("papers/595426-2023-2025-syllabus.pdf") as syllabus_pdf:
        syllabus_parser = SyllabusParser(syllabus_pdf, pages=(12, 46))
        syllabuses = syllabus_parser.parse_syllabus()
    with pdfplumber.open("papers/igcse-biology-0610/0610_w22_qp_42.pdf") as qppdf:
        sq_parser = QuestionPaperParser(qppdf, image_prefix="0610_w22_qp_42")
        questions = sq_parser.parse_question_paper()
    sqms_parser = SQMSParser("papers/igcse-biology-0610/0610_w22_ms_42.pdf", questions)
    questions = sqms_parser.parse_ms()
    classifier = Classifier(syllabuses, cache_path="biology_syllabus_use.pt")
    questions = classifier.classify_all(questions)
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(format_question_hierarchy(questions))
