import re
from dataclasses import dataclass
from PIL import Image
import pdfplumber
from enum import StrEnum
from typing import List, Optional, Tuple
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
        self.question_image = question_image
        self.image = image

    def __str__(self):
        return f"({self.number}): {self.text}" + (f"\n{self.subquestions}")


@dataclass
class MultipleChoiceQuestion:
    def __init__(
        self,
        number: int,
        text: str,
        options: List[str],
        answer: Optional[str] = None,
        image=None,
    ):
        self.number = number
        self.text = text
        self.options = options
        self.answer = answer
        self.image = image

    def __str__(self):
        return f"({self.number}): {self.text}" + (f"\n{self.options}")


class Parser:
    IGNORE_PAGE_FOOTER_Y = 35
    PAGE_NUMBER_Y = 790.4778
    LAST_PAGE_COPYRIGHT_Y = 134
    DIFFERENCE = 5

    def __init__(self, pdf: pdfplumber.PDF):
        self.pdf = pdf
        self.chars = self.read_texts()
        self.find_position_constants()

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

    def find_position_constants(self):
        # This method should be overridden in subclasses
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

    def extract_question_image(
        self,
        start_page: int,
        end_page: int,
        resolution=200,
        margin: int = 20,
    ):
        images = []
        for i in range(start_page, end_page + 1):
            page = self.pdf.pages[i]
            # Crop the image to the question area
            im = (
                page.crop(
                    (
                        self.QUESTION_START_X - margin,
                        margin,
                        page.width - self.QUESTION_START_X + margin,
                        page.height - margin,
                    )
                )
                .to_image(resolution=resolution)
                .original
            )
            images.append(im)

        # If multiple pages, stitch images together vertically
        if len(images) > 1:
            stitched = Image.new(
                "RGB", (images[0].width, sum(im.height for im in images))
            )
            y_offset = 0
            for im in images:
                stitched.paste(im, (0, y_offset))
                y_offset += im.height
            return stitched
        return images[0]

    def extract_image_inpage(
        self,
        page: pdfplumber.page,
    ):
        images = []
        for image in page.images:
            if image["x0"] < self.QUESTION_START_X:
                continue
            if image["x1"] > page.width - self.QUESTION_START_X:
                continue
            if image["top"] < self.IGNORE_PAGE_FOOTER_Y:
                continue
            if image["top"] > page.height - self.IGNORE_PAGE_FOOTER_Y:
                continue
            bbox = (
                image["x0"],
                image["top"],
                image["x1"],
                image["bottom"],
            )
            im = page.within_bbox(bbox).to_image()
            images.append(im)
        return images


class MCQParser(Parser):
    QUESTION_START_X = 49.6063
    DIFFERENCE = 5

    def __init__(self, pdf: pdfplumber.PDF):
        super().__init__(pdf)

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
        print(self.QUESTION_START_X)

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
        start_y = self.chars[start_index]["y"]
        end_y = self.chars[end_index - 1]["y"]
        page = self.chars[start_index]["page"]
        image = self.extract_mcq_image(
            page=page,
            y0=start_y,
            y1=end_y,
            resolution=200,
        )
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
            image=image,  # whole question imag
        )

    def parse_option(self, start_index: int, end_index: int):
        option_text = "".join(
            char["text"] for char in self.chars[start_index:end_index]
        )
        return option_text

    def extract_mcq_image(self, page: int, y0: int, y1: int, resolution=200):
        page = self.pdf.pages[page]
        # convert y0 y1 (from top) to y0 y1 (from bottom)
        y0 = page.height - y0
        y1 = page.height - y1
        im = (
            page.crop(
                (
                    self.QUESTION_START_X - 10,
                    y0 - 20,
                    page.width,
                    y1,
                )  # (x0, top, x1, bottom)
            )
            .to_image(resolution=resolution)
            .original
        )
        return im


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
        image = self.extract_question_image(
            start_page=start_page,
            end_page=end_page,
            resolution=200,
        )
        inside_images = []
        for page in self.pdf.pages[start_page : end_page + 1]:
            page_images = self.extract_image_inpage(page)
            inside_images.extend(page_images)

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
            question_image=inside_images,  # images in the question
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

    def extract_subquestion_image(self, page: int, y0: int, y1: int, resolution=200):
        page = self.pdf.pages[page]
        y0 = page.height - y0
        y1 = page.height - y1
        im = (
            page.crop(
                (
                    self.SUBQUESTION_START_X,
                    y0,
                    page.width,
                    y1,
                )
            )
            .to_image(resolution=resolution)
            .original
        )
        return im


def format_question_hierarchy(questions):
    output = ""
    for q in questions:
        output += f"{q.text}\n"
        if isinstance(q, MultipleChoiceQuestion):
            if q.options:
                output += f"Options: {', '.join(q.options)}\n"
        else:
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
    qp_path = "papers/igcse-biology-0610/0610_w23_qp_12.pdf"
    ms_path = "papers/igcse-biology-0610/0610_w23_ms_42.pdf"
    # extract subject code, exam season, and paper type from the file name
    match = re.search(r"(\d{4})_(\w{3})_(\d{2})", qp_path)
    if match:
        subject_code, exam_season, paper_type = match.groups()
        print(f"Subject Code: {subject_code}")
        print(f"Exam Season: {exam_season}")
        print(f"Paper Type: {paper_type}")

    with open("output.txt", "w", encoding="utf-8") as f:
        # with pdfplumber.open(qp_path) as qp_pdf:
        #     qp_parser = QuestionPaperParser(qp_pdf)
        #     qp_questions = qp_parser.parse_question_paper()
        #     qp_texts = qp_parser.read_texts()
        #     formatted_output = format_question_hierarchy(qp_questions)
        #     f.write(formatted_output)

        with pdfplumber.open(qp_path) as qp_pdf:
            qp_parser = MCQParser(qp_pdf)
            qp_questions = qp_parser.parse_question_paper()
            formatted_output = format_question_hierarchy(qp_questions)
            f.write(formatted_output)

        # with pdfplumber.open(ms_path) as ms_pdf:
        #     ms_parser = MarkSchemeParser(ms_pdf)
        #     lines = ms_parser.extract_lines()
        #     f.write(pprint.pformat(lines, width=80))


if __name__ == "__main__":
    main()
