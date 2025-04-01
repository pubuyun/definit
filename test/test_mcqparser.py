import re
import pdfplumber
from parser import MCQParser
from PIL import Image
import pprint


def format_question_hierarchy(questions):
    output = ""
    for q in questions:
        output += f"{q.text}\n"
        if q.options:
            output += f"Options: {', '.join(q.options)}\n"
        if q.image:
            q.image.save(f"question_{q.number}.png")  # Save the question image
        output += "\n" + "-" * 80 + "\n"
    return output.strip()


def test_mcq_parser(qp_path="papers/igcse-biology-0610/0610_w23_qp_12.pdf"):
    # extract subject code, exam season, and paper type from the file name
    match = re.search(r"(\d{4})_(\w\d{2})_\w{2}_(\d{2})\.pdf", qp_path)
    if match:
        subject_code, exam_season, paper_type = match.groups()
        print(f"Subject Code: {subject_code}")
        print(f"Exam Season: {exam_season}")
        print(f"Paper Type: {paper_type}")

    with open("output.txt", "w", encoding="utf-8") as f:
        with pdfplumber.open(qp_path) as qp_pdf:
            qp_parser = MCQParser(qp_pdf)
            qp_questions = qp_parser.parse_question_paper()
            qp_texts = qp_parser.chars
            formatted_output = format_question_hierarchy(qp_questions)
            f.write(formatted_output)
            f.write(pprint.pformat(qp_texts))


if __name__ == "__main__":
    test_mcq_parser()
