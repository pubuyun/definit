from parser.qp_parser import Parser
from parser.models.question import Question, SubQuestion, SubSubQuestion
import re


class QuestionPaperParser(Parser):
    ROMAN_NUMERALS = [
        "i",
        "ii",
        "iii",
        "iv",
        "v",
        "vi",
        "vii",
        "viii",
        "ix",
        "x",
    ]
    QUESTION_START_X = 49.6063
    SUBQUESTION_START_X = 72
    SUBSUBQUESTION_STARTS = (90, 100)
    question_parsing: int = 0
    subquestion_parsing: str = "z"

    def join_chars(self, start_index: int, end_index: int) -> str:
        result = []
        for i in range(start_index, end_index):
            char = self.chars[i]
            if i > start_index:
                prev_char = self.chars[i - 1]
                if abs(char["y"] - prev_char["y"]) > 1:
                    result.append(" ")
            result.append(char["text"])
        return "".join(result)

    def find_position_constants(self):
        bold_chars = [char for char in self.chars if char["bold"]]
        if len(bold_chars) == 0:
            # from 2024 papers onwards, there is no font information
            bold_chars = self.chars
        bold_strings = "".join(char["text"] for char in bold_chars)
        # find the first 1
        first_one_index = bold_strings.index("1")
        first_one_char = bold_chars[first_one_index]
        self.QUESTION_START_X = first_one_char["x"]
        print(self.QUESTION_START_X)
        try:
            # find the first (a)
            first_a_index = bold_strings.index("(a)")
            first_a_char = bold_chars[first_a_index]
            self.SUBQUESTION_START_X = first_a_char["x"]
            # find the first (i)
            first_i_index = bold_strings.index("(i)")
            first_i_char = bold_chars[first_i_index]
            self.SUBSUBQUESTION_STARTS = (
                first_i_char["x"] - 20,
                first_i_char["x"] + 10,
            )
        except:
            pass

    def find_question_starts(self):
        question_starts = []
        current_number = 1
        for i, char in enumerate(self.chars):
            if abs(char["x"] - self.QUESTION_START_X) <= self.DIFFERENCE:
                text = "".join(c["text"] for c in self.chars[i : i + 3])
                if re.match(
                    f"{current_number}",
                    text,
                ):
                    question_starts.append(i)
                    current_number += 1
        return question_starts

    def parse_question(self, start_index: int, end_index: int, number: int):
        start_page = self.chars[start_index]["page"]
        end_page = self.chars[end_index - 1]["page"]
        self.question_parsing = number
        subquestion_starts = self.find_subquestion_starts(start_index, end_index)
        if subquestion_starts:
            subquestions = []
            image_paths = []  # List to store all subquestion image paths
            question_text = self.join_chars(start_index, subquestion_starts[0])
            for i, subquestion_start in enumerate(subquestion_starts):
                if i == len(subquestion_starts) - 1:
                    subquestion_end = end_index
                else:
                    subquestion_end = subquestion_starts[i + 1]
                subquestion = self.parse_subquestion(
                    subquestion_start,
                    subquestion_end,
                    chr(ord("a") + i),
                )
                subquestions.append(subquestion)
                if isinstance(
                    subquestion.image, list
                ):  # If subquestion has subsubquestions
                    image_paths.extend(subquestion.image)
                elif subquestion.image:  # If subquestion has its own image
                    image_paths.append(subquestion.image)
            return Question(
                number=number,
                text=question_text,
                subquestions=subquestions,
                image=image_paths,  # List of all subquestion image paths
            )
        else:
            subquestions = None
            question_text = self.join_chars(start_index, end_index)
            image = self.extract_question_image(
                start_page=start_page,
                end_page=end_page,
                resolution=200,
            )
            # save image
            image_path = f"{self.IMAGE_PATH}{self.image_prefix}_question_{number}.png"
            image.save(image_path)
            return Question(
                number=number,
                text=question_text,
                subquestions=subquestions,
                image=image_path,  # whole question image
            )

    def parse_subquestion(self, start_index: int, end_index: int, number: str):
        subsubquestion_starts = self.find_subsubquestion_starts(start_index, end_index)
        self.subquestion_parsing = number
        if subsubquestion_starts:
            subsubquestions = []
            image_paths = []  # List to store subsubquestion image paths
            subquestion_text = self.join_chars(start_index, subsubquestion_starts[0])
            for i, subsubquestion_start in enumerate(subsubquestion_starts):
                if i == len(subsubquestion_starts) - 1:
                    subsubquestion_end = end_index
                else:
                    subsubquestion_end = subsubquestion_starts[i + 1]
                subsubquestion = self.parse_subsubquestion(
                    subsubquestion_start,
                    subsubquestion_end,
                    self.ROMAN_NUMERALS[i],
                )
                subsubquestions.append(subsubquestion)
                if subsubquestion.image:
                    image_paths.append(subsubquestion.image)
            return SubQuestion(
                number=number,
                text=subquestion_text,
                subsubquestions=subsubquestions,
                image=image_paths,  # List of subsubquestion image paths
            )
        else:
            subsubquestions = None
            subquestion_text = self.join_chars(start_index, end_index)
            # Extract image only if no subsubquestions
            start_y = self.chars[start_index]["y"]
            page = self.chars[start_index]["page"]
            end_y = (
                self.chars[end_index + 1]["y"]
                if end_index < len(self.chars)
                and self.chars[end_index + 1]["page"] == page
                else self.IGNORE_PAGE_FOOTER_Y
            )
            image = self.extract_image_inpage(
                page=page,
                y0=start_y,
                y1=end_y,
                resolution=200,
            )
            image_path = f"{self.IMAGE_PATH}{self.image_prefix}_question{self.question_parsing}_sub_{number}.png"
            image.save(image_path)
            return SubQuestion(
                number=number,
                text=subquestion_text,
                subsubquestions=subsubquestions,
                image=image_path,  # Single image path
            )

    def parse_subsubquestion(self, start_index: int, end_index: int, number: str):
        subsubquestion_text = self.join_chars(start_index, end_index)
        # Extract image for subsubquestion
        start_y = self.chars[start_index]["y"]
        page = self.chars[start_index]["page"]
        end_y = (
            self.chars[end_index + 1]["y"]
            if end_index < len(self.chars) and self.chars[end_index + 1]["page"] == page
            else self.IGNORE_PAGE_FOOTER_Y
        )
        image = self.extract_image_inpage(
            page=page,
            y0=start_y,
            y1=end_y,
            resolution=200,
        )
        image_path = f"{self.IMAGE_PATH}{self.image_prefix}_question_{self.question_parsing}_sub_{self.subquestion_parsing}_subsub_{number}.png"
        image.save(image_path)
        return SubSubQuestion(number=number, text=subsubquestion_text, image=image_path)

    def find_subquestion_starts(self, start_index: int, end_index: int):
        subquestion_starts = []
        current_question_alpha = "a"
        for i in range(start_index, end_index):
            x = self.chars[i]["x"]
            if abs(x - self.SUBQUESTION_START_X) <= self.DIFFERENCE:
                text = "".join(char["text"] for char in self.chars[i : i + 5])
                if re.match(r"\(" + current_question_alpha + r"\)", text):
                    current_question_alpha = chr(ord(current_question_alpha) + 1)
                    subquestion_starts.append(i)
        return subquestion_starts

    def find_subsubquestion_starts(self, start_index: int, end_index: int):
        subsubquestion_starts = []
        current_roman_index = 0
        for i in range(start_index, end_index):
            x = self.chars[i]["x"]
            if (
                self.SUBSUBQUESTION_STARTS[0]
                <= round(x)
                <= self.SUBSUBQUESTION_STARTS[1]
            ):
                text = "".join(char["text"] for char in self.chars[i : i + 5])
                if re.match(
                    r"\(" + self.ROMAN_NUMERALS[current_roman_index] + r"\)",
                    text,
                ):
                    current_roman_index += 1
                    subsubquestion_starts.append(i)
        return subsubquestion_starts


if __name__ == "__main__":
    import pdfplumber
    import re

    def format_question_hierarchy(questions):
        output = ""
        for q in questions:
            output += f"{q.text}\n"
            if q.subquestions:
                for sub_q in q.subquestions:
                    text = sub_q.text.strip()
                    output += f"\n    {text}\n"
                    if sub_q.subsubquestions:
                        for subsub_q in sub_q.subsubquestions:
                            text = subsub_q.text.strip()
                            output += f"\n        {text}\n"
            output += "\n" + "-" * 80 + "\n"
        return output.strip()

    qp_path = "papers/igcse-biology-0610/0610_w23_qp_42.pdf"
    # extract subject code, exam season, and paper type from the file name
    match = re.search(r"(\d{4})_(\w\d{2})_\w{2}_(\d{2})\.pdf", qp_path)
    if match:
        subject_code, exam_season, paper_type = match.groups()
        print(f"Subject Code: {subject_code}")
        print(f"Exam Season: {exam_season}")
        print(f"Paper Type: {paper_type}")

    with open("output.txt", "w", encoding="utf-8") as f:
        with pdfplumber.open(qp_path) as qp_pdf:
            qp_parser = QuestionPaperParser(qp_pdf, image_prefix="0610_w23_qp_42")
            qp_questions = qp_parser.parse_question_paper()
            formatted_output = format_question_hierarchy(qp_questions)
            f.write(formatted_output)
