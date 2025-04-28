from parser.qp_parser import Parser
from parser.models.question import MultipleChoiceQuestion
import re
from PIL import Image


class MCQParser(Parser):
    QUESTION_START_X = 49.6063
    DIFFERENCE = 5
    IGNORE_PAGE_FOOTER_Y = 40

    def find_position_constant(self):
        bold_chars = [char for char in self.chars if char["bold"]]
        if len(bold_chars) == 0:
            # from 2024 papers onwards, there is no font information
            bold_chars = self.chars
        bold_strings = "".join(char["text"] for char in bold_chars)
        # find the first 1
        first_one_index = bold_strings.index("1")
        first_one_char = bold_chars[first_one_index]
        self.QUESTION_START_X = first_one_char["x"]

    def find_question_starts(self):
        question_starts = []
        current_number = 1
        for i, char in enumerate(self.chars):
            if abs(char["x"] - self.QUESTION_START_X) <= self.DIFFERENCE:
                text = "".join(c["text"] for c in self.chars[i : i + 3])
                if re.match(f"{current_number}", text):
                    question_starts.append(i)
                    current_number += 1
        return question_starts

    def find_options(self, start: int, end: int):
        option_starts = []
        current_alpha = "A"
        for i in range(start, end):
            if not self.chars[i]["bold"]:
                continue
            if self.chars[i]["text"] == current_alpha:
                option_starts.append(i)
                current_alpha = chr(ord(current_alpha) + 1)
        return option_starts

    def parse_question(self, start_index: int, end_index: int, number: int):
        start_y = self.chars[start_index + 1]["y"]
        page = self.chars[start_index]["page"]
        end_y = (
            self.chars[end_index + 1]["y"]
            if end_index + 1 < len(self.chars)
            and self.chars[end_index + 1]["page"] == page
            else self.IGNORE_PAGE_FOOTER_Y
        )
        image = self.extract_image_inpage(
            page=page,
            y0=start_y,
            y1=end_y,
            resolution=200,
        )
        image_path = f"{self.IMAGE_PATH}{self.image_prefix}_question_{number}.png"
        image.save(image_path)

        option_starts = self.find_options(start_index, end_index)
        if option_starts:
            options = []
            question_text = "".join(
                char["text"] for char in self.chars[start_index : option_starts[0]]
            )
            for i, option_start in enumerate(option_starts):
                if i == len(option_starts) - 1:
                    option_end = end_index
                else:
                    option_end = option_starts[i + 1]
                options.append(
                    self.parse_option(
                        option_start,
                        option_end,
                    )
                )
        else:
            options = None
            question_text = "".join(
                char["text"] for char in self.chars[start_index:end_index]
            )
        return MultipleChoiceQuestion(
            number=number,
            text=question_text,
            options=options,
            image=image_path,  # whole question image
        )

    def parse_option(self, start_index: int, end_index: int):
        option_text = "".join(
            char["text"] for char in self.chars[start_index:end_index]
        )
        return option_text


if __name__ == "__main__":
    import re
    import pdfplumber

    def format_question_hierarchy(questions):
        output = ""
        for q in questions:
            output += f"{q.text}\n"
            if q.options:
                output += f"Options: {', '.join(q.options)}\n"
            output += "\n" + "-" * 80 + "\n"
        return output.strip()

    qp_path = "papers/igcse-biology-0610/0610_w23_qp_12.pdf"
    # extract subject code, exam season, and paper type from the file name
    match = re.search(r"(\d{4})_(\w\d{2})_\w{2}_(\d{2})\.pdf", qp_path)
    if match:
        subject_code, exam_season, paper_type = match.groups()
        print(f"Subject Code: {subject_code}")
        print(f"Exam Season: {exam_season}")
        print(f"Paper Type: {paper_type}")

    with open("output.txt", "w", encoding="utf-8") as f:
        with pdfplumber.open(qp_path) as qp_pdf:
            qp_parser = MCQParser(qp_pdf, image_prefix="0610_w23_qp_12")
            qp_questions = qp_parser.parse_question_paper()
            qp_texts = qp_parser.chars
            formatted_output = format_question_hierarchy(qp_questions)
            f.write(formatted_output)
