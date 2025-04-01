import re
import pdfplumber
from parser import QuestionPaperParser
from PIL import Image


def format_question_hierarchy(questions):
    output = ""
    for q in questions:
        output += f"{q.text}\n"
        if q.question_image:
            for i, img in enumerate(q.question_image):
                img.save(f"question_{q.number}_image_{i}.png")
        if q.subquestions:
            for sub_q in q.subquestions:
                text = sub_q.text.strip()
                output += f"\n    {text}\n"
                if sub_q.subsubquestions:
                    for subsub_q in sub_q.subsubquestions:
                        text = subsub_q.text.strip()
                        output += f"\n        {text}\n"
        if q.image:
            q.image.save(f"question_{q.number}.png")  # Save the question image
        output += "\n" + "-" * 80 + "\n"
    return output.strip()


def test_structured_paper(qp_path="papers/igcse-biology-0610/0610_w23_qp_12.pdf"):
    # extract subject code, exam season, and paper type from the file name
    match = re.search(r"(\d{4})_(\w\d{2})_\w{2}_(\d{2})\.pdf", qp_path)
    if match:
        subject_code, exam_season, paper_type = match.groups()
        print(f"Subject Code: {subject_code}")
        print(f"Exam Season: {exam_season}")
        print(f"Paper Type: {paper_type}")

    with open("output.txt", "w", encoding="utf-8") as f:
        with pdfplumber.open(qp_path) as qp_pdf:
            qp_parser = QuestionPaperParser(qp_pdf)
            qp_questions = qp_parser.parse_question_paper()
            formatted_output = format_question_hierarchy(qp_questions)
            f.write(formatted_output)


if __name__ == "__main__":
    test_structured_paper()
