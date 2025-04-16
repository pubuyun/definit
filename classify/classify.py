from parser.models.question import (
    Question,
    SubQuestion,
    SubSubQuestion,
    MultipleChoiceQuestion,
)
from parser.models.syllabus import Syllabus
from typing import Any, Dict, List, Optional, Tuple
import re
from transformers import AutoTokenizer, AutoModel
import torch
from torch.nn.functional import cosine_similarity
import tqdm
import hashlib

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = AutoTokenizer.from_pretrained("allenai/scibert_scivocab_uncased")
model = AutoModel.from_pretrained("allenai/scibert_scivocab_uncased")
model = model.to(device)
model.eval()


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

        embeddings = []
        for i in tqdm.tqdm(range(len(all_points)), desc="Calculating embeddings"):
            embedding = self.get_sentence_embedding(all_points[i])
            embeddings.append(embedding.cpu())

        return torch.stack(embeddings).to(device), syllabus_indices

    def _save_cache(self, current_hash: str) -> None:
        cache_data = {
            "hash": current_hash,
            "embeddings": self.syllabus_embeddings.cpu(),
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
            self.syllabus_embeddings = cache_data["embeddings"].to(device)
            self.syllabus_mapping = cache_data["syllabus_indices"]
            return True
        except Exception as e:
            print(f"Cache load failed: {str(e)}")
            return False

    @staticmethod
    def get_sentence_embedding(sentence: str) -> torch.Tensor:
        raw_segments = [s.strip() for s in re.split(r"/|;|\.", sentence) if s.strip()]
        valid_segments = [s for s in raw_segments if len(s) >= 3]
        if not valid_segments:
            valid_segments = [sentence] if len(sentence) >= 3 else [sentence + "[UNK]"]

        embeddings = []
        with torch.no_grad():
            for seg in valid_segments:
                inputs = tokenizer(
                    seg.lower(),
                    return_tensors="pt",
                    truncation=True,
                    padding=True,
                    max_length=512,
                ).to(device)
                outputs = model(**inputs)
                embeddings.append(outputs.last_hidden_state[:, 0, :])
        if embeddings:
            stacked = torch.stack(embeddings)
            return torch.mean(stacked, dim=0).squeeze()
        else:
            inputs = tokenizer(
                sentence.lower(),
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512,
            ).to(device)
            return model(**inputs).last_hidden_state[:, 0, :].squeeze()

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
        # remove more than three connected dots, remove score
        question_sentence = re.sub(r"\.{3,}", "", question_sentence)
        question_sentence = re.sub(r"\[\d+\]", "", question_sentence)

        question_embedding = self.get_sentence_embedding(question_sentence)
        similarities = cosine_similarity(
            question_embedding.unsqueeze(0),
            self.syllabus_embeddings,
            dim=1,
        )
        # get max 5 similarities
        max_indices = torch.topk(similarities, 5).indices
        # get syllabuses with max similarities
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
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(format_question_hierarchy(questions))
