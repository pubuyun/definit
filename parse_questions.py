import re
from dataclasses import dataclass
from PIL import Image
import pdfplumber
from enum import StrEnum
from typing import List, Optional, Tuple
import turtle
import pprint


@dataclass
class MarkScheme:
    def __init__(self, answers: str, guidance: Optional[str]):
        self.answers = answers
        self.guidance = guidance

    def __str__(self):
        output = self.answers
        if self.guidance:
            output += f"\nGuidance: {self.guidance}"
        return output


@dataclass
class SubSubQuestion:
    def __init__(
        self,
        number: str,
        text: str,
        marks: int = 0,
        answer: Optional[MarkScheme] = None,
    ):
        self.number = number
        self.text = text
        self.marks = marks
        self.answer = answer

    def __str__(self):
        return self.text


@dataclass
class SubQuestion:
    def __init__(
        self,
        number: str,
        text: str,
        subsubquestions: Optional[List[SubSubQuestion]],
        marks: int = 0,
        answer: Optional[MarkScheme] = None,
    ):
        self.number = number
        self.text = text
        self.subsubquestions = subsubquestions
        self.answer = answer
        self.marks = marks

    def __str__(self):
        return self.text + (f"\n{self.subsubquestions}")


@dataclass
class Question:
    def __init__(
        self,
        number: int,
        text: str,
        subquestions: List[SubQuestion],
        marks: int = 0,
        answer: Optional[MarkScheme] = None,
        question_image=None,  # images in the question
        image=None,  # image of the whole question
    ):
        self.number = number
        self.text = text
        self.subquestions = subquestions
        self.marks = marks
        self.answer = answer

    def __str__(self):
        return f"({self.number}): {self.text}" + (f"\n{self.subquestions}")


class ParserError(Exception):
    pass


class QuestionPaperParser:
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
    IGNORE_PAGE_FOOTER_Y = 35
    PAGE_NUMBER_Y = 790.4778
    LAST_PAGE_COPYRIGHT_Y = 134
    DIFFERENCE = 5

    def __init__(self, pdf: pdfplumber.PDF):
        self.pdf = pdf
        self.chars = self.read_texts()
        self.find_position_constants()

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

    def parse_question_paper(self):
        questions = []
        question_starts = self.find_question_starts()
        for i, question_start in enumerate(question_starts):
            if i == len(question_starts) - 1:
                question_end = len(self.chars)
            else:
                question_end = question_starts[i + 1]
            question = self.parse_question(question_start, question_end, i + 1)
            questions.append(question)
        return questions

    def read_texts(self):
        chars = []
        for i, page in enumerate(self.pdf.pages[1:]):
            if re.search(r"BLANK PAGE", page.extract_text()):
                continue
            page_chars = page.chars
            page_chars = list(
                filter(
                    lambda x: x["y0"]
                    > (
                        self.IGNORE_PAGE_FOOTER_Y
                        if (i != len(self.pdf.pages) - 2)
                        else self.LAST_PAGE_COPYRIGHT_Y
                    )
                    and x["y0"] != self.PAGE_NUMBER_Y
                    and len(x["text"]) == 1,
                    page_chars,
                )
            )
            chars.extend(
                [
                    {
                        "x": char["x0"],
                        "y": char["y0"],
                        "text": char["text"],
                        "bold": "bold" in char["fontname"].lower(),
                        "page": i + 1,
                    }
                    for char in page_chars
                ]
            )
        return chars

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
        question_start = (
            int(self.chars[start_index]["page"]),
            int(self.chars[start_index]["y"]),
        )  # page, y
        question_end = (
            int(self.chars[end_index - 1]["page"]),
            int(self.chars[end_index - 1]["y"]),
        )
        image = self.extract_question_image(
            start_page=question_start[0],
            end_page=question_end[0],
            start_y=question_start[1],
            end_y=question_end[1],
        )

        subquestion_starts = self.find_subquestion_starts(start_index, end_index)
        if subquestion_starts:
            subquestions = []
            question_text = "".join(
                char["text"] for char in self.chars[start_index : subquestion_starts[0]]
            )
            for i, subquestion_start in enumerate(subquestion_starts):
                if i == len(subquestion_starts) - 1:
                    subquestion_end = end_index
                else:
                    subquestion_end = subquestion_starts[i + 1]
                subquestions.append(
                    self.parse_subquestion(
                        subquestion_start,
                        subquestion_end,
                        chr(ord("a") + i),
                    )
                )
        else:
            subquestions = None
            question_text = "".join(
                char["text"] for char in self.chars[start_index:end_index]
            )
        return Question(
            number=number,
            text=question_text,
            subquestions=subquestions,
            image=image,  # whole question image
        )

    def parse_subquestion(self, start_index: int, end_index: int, number: str):
        subsubquestion_starts = self.find_subsubquestion_starts(start_index, end_index)
        if subsubquestion_starts:
            subsubquestions = []
            subquestion_text = "".join(
                char["text"]
                for char in self.chars[start_index : subsubquestion_starts[0]]
            )
            for i, subsubquestion_start in enumerate(subsubquestion_starts):
                if i == len(subsubquestion_starts) - 1:
                    subsubquestion_end = end_index
                else:
                    subsubquestion_end = subsubquestion_starts[i + 1]
                subsubquestions.append(
                    self.parse_subsubquestion(
                        subsubquestion_start,
                        subsubquestion_end,
                        self.ROMAN_NUMERALS[i],
                    )
                )
        else:
            subsubquestions = None
            subquestion_text = "".join(
                char["text"] for char in self.chars[start_index:end_index]
            )
        return SubQuestion(
            number=number,
            text=subquestion_text,
            subsubquestions=subsubquestions,
        )

    def parse_subsubquestion(self, start_index: int, end_index: int, number: str):
        subsubquestion_text = "".join(
            char["text"] for char in self.chars[start_index:end_index]
        )
        return SubSubQuestion(number=number, text=subsubquestion_text)

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

    def extract_question_image(
        self,
        start_page: int,
        end_page: int,
        start_y: int,
        end_y: int,
        resolution: int = 150,
    ):
        """Extract a section of the PDF as an image between specified pages and y-coordinates.

        Args:
            start_page: Starting page number (1-based indexing)
            end_page: Ending page number (1-based indexing)
            start_y: Starting y-coordinate on the first page
            end_y: Ending y-coordinate on the last page
            resolution: DPI resolution for the output image (default: 150)

        Returns:
            PIL Image object of the extracted region
        """
        margin = 20
        resmul = 3
        # Get page dimensions from first page
        page = self.pdf.pages[0]
        page_width = int(page.width)
        image_width = page_width * resmul
        # Adjust coordinates for margin
        x0 = margin
        x1 = page_width - margin
        y0 = start_y
        y1 = end_y

        # Extract images from each page in range
        images = []
        heights = []
        for page_num in range(start_page - 1, end_page):
            page = self.pdf.pages[page_num]
            # For first page use start_y, for last page use end_y, otherwise full height
            if page_num == start_page - 1:
                crop_y0 = y0
                crop_y1 = int(page.height)
            elif page_num == end_page - 1:
                crop_y0 = 0
                crop_y1 = y1
            else:
                crop_y0 = 0
                crop_y1 = int(page.height)

            # Crop and get image at resolution
            cropped = page.crop((x0, crop_y0, x1, crop_y1))
            im = cropped.to_image(resolution=resolution)

            # Calculate target size
            target_height = int((crop_y1 - crop_y0) * resolution / 72)
            # Resize to match target dimensions
            im = im.resize((image_width, target_height), Image.Resampling.LANCZOS)
            images.append(im)
            heights.append(target_height)

        # If multiple pages, stitch images together vertically
        if len(images) > 1:
            total_height = sum(im.height for im in images)
            combined = Image.new("RGB", (image_width, total_height))
            y_offset = 0
            for im in images:
                combined.paste(im, (0, y_offset))
                y_offset += im.height
            return combined

        return images[0]


def format_question_hierarchy(questions):
    output = ""
    for q in questions:
        output += f"{q.text}\n"
        if q.image:
            q.image.save(f"question_{q.number}.png")  # Save the question image
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


class MarkSchemeParser:
    def __init__(self, pdf: pdfplumber.PDF):
        self.pdf = pdf

    def extract_lines(self):
        lines = []
        for page in self.pdf.pages[5:]:
            page_lines = [(rect["x0"], rect["y0"]) for rect in page.rects]
            lines.append(page_lines)
        return lines


def main():
    qp_path = "papers/igcse-chemistry-0620/0620_w23_qp_63.pdf"
    ms_path = "papers/igcse-biology-0610/0610_w23_ms_42.pdf"

    with open("output.txt", "w", encoding="utf-8") as f:
        with pdfplumber.open(qp_path) as qp_pdf:
            qp_parser = QuestionPaperParser(qp_pdf)
            qp_questions = qp_parser.parse_question_paper()
            qp_texts = qp_parser.read_texts()
            formatted_output = format_question_hierarchy(qp_questions)
            f.write(pprint.pformat(qp_texts))
            f.write(formatted_output)
        # with pdfplumber.open(ms_path) as ms_pdf:
        #     ms_parser = MarkSchemeParser(ms_pdf)
        #     lines = ms_parser.extract_lines()
        #     f.write(pprint.pformat(lines, width=80))


if __name__ == "__main__":
    main()
