from dotenv import load_dotenv
from parser.models.question import (
    Question,
    SubQuestion,
    SubSubQuestion,
    MultipleChoiceQuestion,
)

load_dotenv()
from parser.models.syllabus import Syllabus
from parser.sq_ms_parser import SQMSParser
from parser.sq_parser import QuestionPaperParser
from parser.mcq_ms_parser import MCQMSParser
from parser.mcq_parser import MCQParser
from parser.syllabus_parser import SyllabusParser
import pdfplumber
from typing import List, Optional
from urllib.parse import urljoin
import re
import tqdm
import os
import json
import requests


class LLMClassifier:
    GUIDE = """
    你是一个考试大纲分类器, 你需要把考试问题分类到考试大纲中. 你有一个考试大纲和一组考试问题. 考试问题可能是多层嵌套的, 你需要把每个最小问题都分类到考试大纲中. 你只需要分类最小的问题单位(带Answer:), 不需要分类父问题.
    输入格式为Number:{question_number} Text:{question_description}( Answer:{question_answer}) 输出格式为{question_number(如果有父问题, 组合number, 用空格连接)}:{syllabus_number},每个question占一行, 不需要输出多余信息.
    """

    def __init__(
        self,
        api_key: str,
        api_url: str,
        syllabuses: List[Syllabus],
    ):
        self.syllabus = syllabuses
        self.syllabus_str = "\n\n".join([str(syl) for syl in syllabuses]) + "\n\n"
        self.api_key = api_key
        self.api_url = api_url

    def classify_all(
        self, questions: List[Question | MultipleChoiceQuestion]
    ) -> List[Question | MultipleChoiceQuestion]:
        if isinstance(questions[0], MultipleChoiceQuestion):
            text = self.format_mcq(questions)
        else:
            text = self.format_structured_question(questions)
        content = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": self.GUIDE,
                },
                {
                    "role": "user",
                    "content": f"{self.syllabus_str}",
                },
                {
                    "role": "user",
                    "content": "Number:1 Text:1 Which process provides an organism with the raw materials needed for tissue repair?  Options: A excretion , B growth , C nutrition , D respiration   ",
                },
                {
                    "role": "assistant",
                    "content": "1:1.1",
                },
                {
                    "role": "user",
                    "content": """Number:4 Text:4
    Number:a Text:(a) Fig. 4.1 is a flow chart showing some of the processes that occur in a biofuels power plant. crop wasteforestry waste pretreatment of biomass the giant reed plant, Arundo donax, is grown for biomass complex carbohydrates released from biomass release of sugars, including glucose breakdown by enzymes fermentation by yeast ethanol biofuel Fig. 4.1
        Number:i Text: (i) The fermentation stage shown in Fig. 4.1 requires yeast.    Complete the balanced chemical equation to show how ethanol is produced by yeast  respiration.       + Answer:C6H12O6  ;            2C2H5OH + 2CO2;""",
                },
                {
                    "role": "assistant",
                    "content": "4 a i:12.3",
                },
                {
                    "role": "user",
                    "content": f"{text}",
                },
            ],
            "temperature": 0,
            "max_tokens": 2000,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            urljoin(self.api_url, "/chat/completions"), headers=headers, json=content
        )
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                answer = result["choices"][0]["message"]["content"]
                print(answer)
                lines = answer.strip().split("\n")
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(":")
                    if len(parts) != 2:
                        print(f"Error: {line}")
                        continue
                    question_number, syllabus_number = parts
                    question_number = question_number.strip()
                    syllabus_number = syllabus_number.strip()
                    question_number_list = question_number.split(" ")
                    syllabus = self.find_syllabus(syllabus_number)
                    if not syllabus:
                        print(f"Error: {syllabus_number} not found in syllabus")
                        continue
                    if not self.assign_to_question(
                        syllabus,
                        questions,
                        int(question_number_list[0]),
                        (
                            question_number_list[1]
                            if len(question_number_list) > 1
                            else None
                        ),
                        (
                            question_number_list[2]
                            if len(question_number_list) > 2
                            else None
                        ),
                    ):
                        print(f"Error: {question_number} not found in questions")
                return questions
            else:
                print(f"Error: {result}")
        else:
            print(f"Error: {response.status_code} - {response.text}")

    def find_syllabus(self, syllabus_number: str) -> Optional[Syllabus]:
        for syllabus in self.syllabus:
            if syllabus.number == syllabus_number:
                return syllabus
        return None

    @staticmethod
    def format_structured_question(questions: List[Question]) -> str:
        output = ""
        sub = lambda s: re.sub(
            r"\.{3,}", "", re.sub(r"\[(\d+|(Total: \d+))\]", "", s)
        ).strip()
        for q in questions:
            output += f"Number:{q.number} Text:{sub(q.text)}"
            if q.subquestions:
                output += "\n"
                for sub_q in q.subquestions:
                    text = sub_q.text
                    output += f"    Number:{sub_q.number} Text:{sub(text)}"
                    if sub_q.subsubquestions:
                        output += "\n"
                        for subsub_q in sub_q.subsubquestions:
                            text = subsub_q.text
                            output += f"        Number:{subsub_q.number} Text: {sub(text)} Answer:{subsub_q.answer or ''}\n"
                    else:
                        output += f" Answer:{sub_q.answer or ''}\n"
            else:
                output += f" Answer:{q.answer or ''}\n"
            output += "\n" + "-" * 80 + "\n"
        return output

    @staticmethod
    def format_mcq(questions: List[MultipleChoiceQuestion]) -> str:
        output = ""
        for q in questions:
            output += f"Number:{q.number} Text:{q.text}"
            if q.options:
                output += f" Options: {', '.join(q.options)}"
            if q.answer:
                output += f" Answer: {q.answer}"
            output += "\n\n"
        return output.strip()

    def assign_to_question(
        self,
        syllabus: Syllabus,
        questions: List[Question] | List[MultipleChoiceQuestion],
        question_number: int,
        subquestion_number: Optional[str] = None,
        subsubquestion_number: Optional[str] = None,
    ) -> bool:
        # Find matching question
        matching_question = next(
            filter(lambda q: q.number == question_number, questions), None
        )
        if not matching_question:
            return False

        # If no subquestion, assign directly to question
        if not subquestion_number:
            matching_question.syllabus = (
                syllabus
                if isinstance(matching_question, MultipleChoiceQuestion)
                else [syllabus]
            )
            return True

        # Find matching subquestion
        matching_subquestion = next(
            (
                filter(
                    lambda sq: sq.number == subquestion_number,
                    matching_question.subquestions,
                )
            ),
            None,
        )
        if not matching_subquestion:
            return False

        # If no subsubquestion, assign to subquestion
        if not subsubquestion_number:
            matching_subquestion.syllabus = [syllabus]
            matching_question.syllabus.append(syllabus)
            return True

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
            matching_subsubquestion.syllabus = [syllabus]
            matching_subquestion.syllabus.append(syllabus)
            matching_question.syllabus.append(syllabus)
            return True
        return False


if __name__ == "__main__":
    issq = input("Test SQ? (y/n): ").strip().lower() == "y"
    if issq:
        with pdfplumber.open("papers/595426-2023-2025-syllabus.pdf") as syllabus_pdf:
            syllabus_parser = SyllabusParser(syllabus_pdf, pages=(12, 46))
            syllabuses = syllabus_parser.parse_syllabus()
        with pdfplumber.open("papers/igcse-biology-0610/0610_w22_qp_42.pdf") as qppdf:
            sq_parser = QuestionPaperParser(qppdf, image_prefix="0610_w22_qp_42")
            questions = sq_parser.parse_question_paper()
        sqms_parser = SQMSParser(
            "papers/igcse-biology-0610/0610_w22_ms_42.pdf", questions
        )
        questions = sqms_parser.parse_ms()

        apikey = os.getenv("API_KEY")
        apiurl = os.getenv("API_URL")
        classifier = LLMClassifier(apikey, apiurl, syllabuses)

        def format_sq_syllabus(
            questions: List[Question], syllabuses: List[Syllabus]
        ) -> str:
            output = ""
            sub = lambda s: re.sub(
                r"\.{3,}", "", re.sub(r"\[(\d+|(Total: \d+))\]", "", s)
            ).strip()
            for q in questions:
                output += f"Number:{q.number} Text:{sub(q.text)}\nSyllabus: {q.syllabus.title if q.syllabus else 'Unknown'}"
                if q.subquestions:
                    output += "\n"
                    for sub_q in q.subquestions:
                        text = sub_q.text
                        output += f"    Number:{sub_q.number} Text:{sub(text)}\n    Syllabus: {sub_q.syllabus.title if sub_q.syllabus else 'Unknown'}"
                        if sub_q.subsubquestions:
                            output += "\n"
                            for subsub_q in sub_q.subsubquestions:
                                text = subsub_q.text
                                output += f"        Number:{subsub_q.number} Text: {sub(text)} Answer:{subsub_q.answer or ''}\n        Syllabus: {subsub_q.syllabus.title if subsub_q.syllabus else 'Unknown'}\n"
                        else:
                            output += f" Answer:{sub_q.answer or ''}\n"
                else:
                    output += f" Answer:{q.answer or ''}\n"
                output += "\n" + "-" * 80 + "\n"
            return output

        with open("output.txt", "w", encoding="utf-8") as f:
            # f.write(LLMClassifier.format_structured_question(questions))
            questions = classifier.classify_all(questions)
            f.write(format_sq_syllabus(questions, syllabuses))
    else:
        with pdfplumber.open("papers/595426-2023-2025-syllabus.pdf") as syllabus_pdf:
            syllabus_parser = SyllabusParser(syllabus_pdf, pages=(12, 46))
            syllabuses = syllabus_parser.parse_syllabus()
        with pdfplumber.open("papers/igcse-biology-0610/0610_w22_qp_12.pdf") as qppdf:
            mcq_parser = MCQParser(qppdf, image_prefix="0610_w22_qp_12")
            questions = mcq_parser.parse_question_paper()
        mcqms_parser = MCQMSParser(
            "papers/igcse-biology-0610/0610_w22_ms_12.pdf", questions
        )
        mcqms_parser.parse_no_error()
        apikey = os.getenv("API_KEY")
        apiurl = os.getenv("API_URL")
        classifier = LLMClassifier(apikey, apiurl, syllabuses)

        def format_mcq_syllabus(
            questions: List[MultipleChoiceQuestion], syllabuses: List[Syllabus]
        ) -> str:
            output = ""
            sub = lambda s: re.sub(
                r"\.{3,}", "", re.sub(r"\[(\d+|(Total: \d+))\]", "", s)
            ).strip()
            for q in questions:
                output += f"Number:{q.number} Text:{sub(q.text)}\nSyllabus: {q.syllabus.title if q.syllabus else 'Unknown'}"
                if q.options:
                    output += f" Options: {', '.join(q.options)}"
                if q.answer:
                    output += f" Answer: {q.answer}"
                output += "\n\n"
            return output.strip()

        with open("output.txt", "w", encoding="utf-8") as f:
            # f.write(LLMClassifier.format_structured_question(questions))
            questions = classifier.classify_all(questions)
            f.write(format_mcq_syllabus(questions, syllabuses))
