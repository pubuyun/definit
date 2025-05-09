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
from pymongo import MongoClient
from bson import ObjectId

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")

CONFIGS = {
    "igcse-biology-0610": {
        "syllabus_path": "papers/595426-2023-2025-syllabus.pdf",
        "syllabus_page_range": (12, 46),
    },
}

client = MongoClient("mongodb://120.25.192.109:27017/")


def convert_obj(obj: Optional[object]) -> Optional[dict]:
    # convert hierarchical object to dict
    if obj is None:
        return None
    if isinstance(obj, list):
        return [convert_obj(item) for item in obj]
    if isinstance(obj, dict):
        return {key: convert_obj(value) for key, value in obj.items()}
    if isinstance(obj, ObjectId):
        return str(obj)
    if hasattr(obj, "__dict__"):
        obj_dict = obj.__dict__
        return {key: convert_obj(value) for key, value in obj_dict.items()}
    return obj


def parse(
    classifier: LLMClassifier, question_paper: str, markscheme: str, issq: bool
) -> List[Question] | List[MultipleChoiceQuestion]:
    with pdfplumber.open(question_paper) as qppdf:
        issq = "Multiple Choice" not in qppdf.pages[0].extract_text()
        if issq:
            sq_parser = QuestionPaperParser(
                qppdf, image_prefix=os.path.basename(question_paper)[:-4]
            )
            questions = sq_parser.parse_question_paper()
            sqms_parser = SQMSParser(
                markscheme,
                questions,
                image_prefix=os.path.basename(question_paper)[:-4],
            )
            questions = sqms_parser.parse_ms()
            questions = classifier.classify_all(questions)
            return questions
        else:
            mcq_parser = MCQParser(
                qppdf, image_prefix=os.path.basename(question_paper)[:-4]
            )
            questions = mcq_parser.parse_question_paper()
            mcqms_parser = MCQMSParser(
                markscheme,
                questions,
                image_prefix=os.path.basename(question_paper)[:-4],
            )
            mcqms_parser.parse_no_error()
            questions = classifier.classify_all(questions)
            return questions


print("\n".join(config for config in CONFIGS.keys()))
subject = input("Select a config: ")
config = CONFIGS[subject]
syllabus_path = config["syllabus_path"]
syllabus_page_range = config["syllabus_page_range"]
database = client[subject]

with pdfplumber.open(syllabus_path) as pdf:
    syllabuses = SyllabusParser(pdf, syllabus_page_range).parse_syllabus()

classifier = LLMClassifier(syllabuses=syllabuses, api_key=API_KEY, api_url=API_URL)

for f in os.listdir("papers/igcse-biology-0610"):
    if "qp" not in f:
        continue

    question_paper = os.path.join("papers/igcse-biology-0610", f)
    markscheme = question_paper.replace("qp", "ms")
    print("Processing", question_paper)

    if not os.path.exists(markscheme):
        print("Markscheme not found for", question_paper)
        continue

    with pdfplumber.open(question_paper, pages=[1]) as qppdf:
        issq = "Multiple Choice" not in qppdf.pages[0].extract_text()

    collection_name = os.path.basename(question_paper)[:-4] + "_sq" if issq else "_mcq"
    if database[collection_name].count_documents({}) > 0:
        print("Already processed", question_paper)
        continue

    questions = parse(classifier, question_paper, markscheme, issq)

    collection = database[collection_name]
    for question in questions:
        question_dict = convert_obj(question)
        collection.insert_one(question_dict)
