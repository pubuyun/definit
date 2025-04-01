from parser import Parser
from .models.question import MultipleChoiceQuestion
import re
from PIL import Image


class MCQParser(Parser):
    QUESTION_START_X = 49.6063
    DIFFERENCE = 5
    IGNORE_PAGE_FOOTER_Y = 40

    def __init__(self, pdf):
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
        start_y = self.chars[start_index + 1]["y"]
        page = self.chars[start_index]["page"]
        end_y = next(
            char["y"] for char in self.chars[end_index::-1] if char["page"] == page
        )

        print(
            f"number: {number}, start_y: {self.chars[start_index]}, end_y: {self.chars[end_index - 1]}"
        )
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
            image=image,  # whole question image
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
        if y1 > page.height - self.IGNORE_PAGE_FOOTER_Y:
            y1 = page.height - self.IGNORE_PAGE_FOOTER_Y
        im = (
            page.crop(
                (
                    self.QUESTION_START_X - 10,
                    y0 - 20,
                    page.width,
                    y1 - 10,
                )  # (x0, top, x1, bottom)
            )
            .to_image(resolution=resolution)
            .original
        )
        return im
