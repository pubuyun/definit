from parser.models import Syllabus
import pdfplumber
from typing import Dict, List, Optional
import re
import pprint


class SyllabusParser:
    PAGES = (12, 46)
    CORE_START_X = 62
    SUPPLEMENT_START_X = 308
    IGNORE_PAGE_FOOTER_Y = 30
    IGNORE_HEADER_Y = 760
    TITLE_PATTERN = r"(?<!\.)(\d+)\s*([A-Za-z\s]+)"
    SUBTITLE_PATTERN = r"\d+\.(\d+)\s*([A-Za-z\s]+)"

    def __init__(self, pdf: pdfplumber.PDF, pages: Optional[tuple] = None):
        self.pdf = pdf
        self.PAGES = pages if pages else self.PAGES
        self.chars = self.read_texts()

    def read_texts(self):
        chars = []
        for i, page in enumerate(self.pdf.pages[self.PAGES[0] - 1 : self.PAGES[1]]):
            if re.search(r"BLANK PAGE", page.extract_text()):
                continue
            page_chars = page.chars
            page_chars = list(
                filter(
                    lambda x: self.IGNORE_HEADER_Y
                    > x["y0"]
                    > (self.IGNORE_PAGE_FOOTER_Y)
                    and len(x["text"]) == 1,
                    page_chars,
                )
            )
            chars.extend(
                [
                    {
                        "index": len(chars) + j,
                        "x": char["x0"],
                        "y": char["y0"],
                        "text": char["text"],
                        "bold": "bold" in char["fontname"].lower(),
                        "page": i + 1,
                    }
                    for j, char in enumerate(page_chars)
                ]
            )

        return chars

    def parse_syllabus(self):
        syllabuses = []
        title_starts = self.find_title_starts()
        for i, title_start in enumerate(title_starts):
            syllabuses.extend(
                self.parse_syllabus_from_title(
                    title_start,
                    (
                        title_starts[i + 1]
                        if i + 1 < len(title_starts)
                        else len(self.chars)
                    ),
                )
            )
        return syllabuses

    def parse_syllabus_from_title(self, start: int, end: int) -> List[Syllabus]:
        subtitle_starts = self.find_subtitle_starts(start, end)
        syllabuses = []
        for i, subtitle_start in enumerate(subtitle_starts):
            syllabuses.append(
                self.parse_syllabus_from_subtitle(
                    subtitle_start,
                    (subtitle_starts[i + 1] if i + 1 < len(subtitle_starts) else end),
                )
            )
        return syllabuses

    def parse_syllabus_from_subtitle(self, start: int, end: int) -> Optional[Syllabus]:
        title = "".join(
            [
                char["text"]
                for char in self.chars[
                    start : (end if end < len(self.chars) else len(self.chars))
                ]
                if char["bold"]
            ]
        )
        number = re.search(r"\d+.\d+", title).group(0)
        syllabus = Syllabus(number=number, title=title, content=[])
        # parse content
        point_starts = self.find_point_starts(start, end)
        for i, point_start in enumerate(point_starts):
            raw_content = "".join(
                [
                    char["text"]
                    for char in self.chars[
                        (point_start + 2) : (
                            point_starts[i + 1] if i < len(point_starts) - 1 else end
                        )
                    ]
                ]
            )

            splited = list(
                filter(lambda x: len(x) > 3, re.split(r"\(\w+\)", raw_content))
            )
            syllabus.content.extend(splited)
        return syllabus

    def find_title_starts(self) -> List[int]:
        title_starts = []
        title_number = 1
        bolds = [char for char in filter(lambda x: x["bold"], self.chars)]
        bolds_text = "".join(bold["text"] for bold in bolds)
        for match in re.finditer(self.TITLE_PATTERN, bolds_text):
            if match.group(1) == str(title_number):
                title_starts.append(bolds[match.start()]["index"])
                title_number += 1
        return title_starts

    def find_subtitle_starts(self, start: int, end: int) -> List[int]:
        subtitle_starts = []
        subtitle_number = 1
        bolds_in_range = [char for char in self.chars[start:end] if char["bold"]]
        bold_texts = "".join(bold["text"] for bold in bolds_in_range)
        for i, match in enumerate(re.finditer(self.SUBTITLE_PATTERN, bold_texts)):
            if match and match.group(1) == str(subtitle_number):
                subtitle_starts.append(bolds_in_range[match.start()]["index"])
                subtitle_number += 1
        return subtitle_starts

    def find_point_starts(self, start: int, end: int) -> List[int]:
        point_starts = []
        current_point = 1
        for i in range(start, end):
            # if the char within 20 pixels of the CORE_START_X or SUPPLEMENT_START_X, and it is a number, check for it
            if (
                abs(self.chars[i]["x"] - self.CORE_START_X) < 20
                or abs(self.chars[i]["x"] - self.SUPPLEMENT_START_X) < 20
            ):
                match = re.match(
                    r"\d+", "".join([char["text"] for char in self.chars[i : i + 2]])
                )
                if match and match.group(0) == str(current_point):
                    point_starts.append(i)
                    current_point += 1
        return point_starts


if __name__ == "__main__":
    syallabus_path = "papers/595426-2023-2025-syllabus.pdf"

    with pdfplumber.open(syallabus_path) as pdf:
        syllabus_parser = SyllabusParser(pdf)
        syllabuses = syllabus_parser.parse_syllabus()
        with open("output.txt", "w", encoding="utf-8") as f:
            f.write("\n\n".join([str(syl) for syl in syllabuses]))
