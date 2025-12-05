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
MONGO_URI = os.getenv("MONGO_URI")

CONFIGS = {
    "igcse-biology-0610": {
        "syllabus_path": "papers/595426-2023-2025-syllabus.pdf",
        "syllabus_page_range": (12, 46),
    },
}

client = MongoClient(MONGO_URI)


def map_syllabus_to_id(syllabuses: List[Syllabus]) -> dict:
    return list(map(lambda x: {"id": x.id, "number": x.number}, syllabuses))


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

database["syllabus"].delete_many({})
for syllabus in syllabuses:
    syllabus_dict = convert_obj(syllabus)
    result = database["syllabus"].insert_one(syllabus_dict)
    syllabus.id = result.inserted_id
print(f"Inserted {len(syllabuses)} syllabus items.")
classifier = LLMClassifier(syllabuses=syllabuses, api_key=API_KEY, api_url=API_URL)

question_collection = database["questions"]
squestion_collection = database["sub_questions"]
ssquestion_collection = database["sub_sub_questions"]
mc_question_collection = database["mc_questions"]

error_list = []
reprocess = [
    "0610_s20_qp_31",
    "0610_s22_qp_23",
    "0610_s24_qp_13",
    "0610_w18_qp_33",
    "0610_w19_qp_13",
    "0610_w20_qp_13",
    "0610_w21_qp_33",
    "0610_w21_qp_62",
    "0610_w22_qp_51",
]
for f in os.listdir("papers/igcse-biology-0610"):
    try:
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

        paper_name = os.path.basename(question_paper)[:-4]

        # if database[collection_name].count_documents({}) > 0:
        #     print("Already processed", question_paper)
        #     continue
        if paper_name not in reprocess and (
            question_collection.count_documents({"paper_name": paper_name}) > 0
            or mc_question_collection.count_documents({"paper_name": paper_name}) > 0
        ):
            print("Already processed", question_paper)
            continue

        questions = parse(classifier, question_paper, markscheme, issq)

        for question in questions:
            question.paper_name = paper_name
            if issq:
                squestions = question.subquestions
                question.syllabus = map_syllabus_to_id(question.syllabus)
                question.subquestions = []
                question_dict = convert_obj(question)
                question_res = question_collection.insert_one(question_dict)
                subquestion_ids = []
                for squestion in squestions:
                    squestion.paper_name = paper_name
                    squestion.parent_id = question_res.inserted_id
                    squestion.parent_number = question.number
                    squestion.syllabus = map_syllabus_to_id(squestion.syllabus)

                    ssquestions = squestion.subsubquestions
                    squestion.subsubquestions = []
                    squestion_dict = convert_obj(squestion)
                    squestion_res = squestion_collection.insert_one(squestion_dict)

                    subsubquestion_ids = []
                    for ssquestion in ssquestions:
                        ssquestion.paper_name = paper_name
                        ssquestion.parent_id = squestion_res.inserted_id
                        ssquestion.parent_number = squestion.number
                        ssquestion.syllabus = map_syllabus_to_id(ssquestion.syllabus)
                        ssquestion_dict = convert_obj(ssquestion)
                        ssquestion_result = ssquestion_collection.insert_one(
                            ssquestion_dict
                        )
                        subsubquestion_ids.append(ssquestion_result.inserted_id)

                    if subsubquestion_ids:
                        squestion_collection.update_one(
                            {"_id": squestion_res.inserted_id},
                            {"$set": {"subsubquestions": subsubquestion_ids}},
                        )

                    subquestion_ids.append(squestion_res.inserted_id)

                if subquestion_ids:
                    question_collection.update_one(
                        {"_id": question_res.inserted_id},
                        {"$set": {"subquestions": subquestion_ids}},
                    )
            else:
                question.paper_name = paper_name
                question.syllabus = map_syllabus_to_id(question.syllabus)
                question_dict = convert_obj(question)
                mc_question_collection.insert_one(question_dict)

        # collection = database[collection_name]
        # for question in questions:
        #     question_dict = convert_obj(question)
        #     collection.insert_one(question_dict)
    except Exception as e:
        print("Error processing", question_paper, ":", str(e))
        error_list.append((question_paper, str(e)))
        continue

with open("error_log.txt", "w") as f:
    for error in error_list:
        f.write(f"{error[0]}: {error[1]}\n")
