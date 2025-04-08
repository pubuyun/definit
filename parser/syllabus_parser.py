from parser.models import Syllabus
import pdfplumber
from typing import Dict, List, Optional
import re


class SyllabusParser:
    PAGES = (12, 46)  # inclusive

    def __init__(self, pdf: pdfplumber.PDF):
        self.pdf = pdf
        self.chars = self.read_texts()

    CORE_START_X = 50
    SUPPLEMENT_START_X = 200
    IGNORE_FOOTER_Y = 50
    IGNORE_HEADER_Y = 700
    TITLE_PATTERN = r"(\d+)\s+([A-Za-z0-9\s]+)"
    SUBTITLE_PATTERN = r"(\d+\.\d+)\s+([A-Za-z0-9\s]+)"

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

    def find_syallbus_starts(self):
        # This method should be overridden in subclasses
        pass

    def find_subtitle_starts(self, start: int, end: int) -> List[int]:
        # This method should be overridden in subclasses
        pass

    def find_point_starts(self, start: int, end: int) -> List[int]:
        # This method should be overridden in subclasses
        pass

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

    def parse_syllabus_from_subtitle(self, start: int, end: int) -> Optional[Syllabus]:
        title = self.parse_subtitle(start)
        if not title:
            return None
        syllabus = Syllabus(title=title)
        # parse content
        point_starts = self.find_point_starts(start, end)
        for i, point_start in enumerate(point_starts):
            syllabus.content.append(
                "".join(
                    [
                        char["text"]
                        for char in self.chars[
                            point_start : (
                                point_starts[i + 1]
                                if i < len(point_starts) - 1
                                else end
                            )
                        ]
                    ]
                )
            )
        return syllabus

    def parse_subtitle(self, start: int) -> str:
        # re.match(self.TITLE_PATTERN, self.chars[start]["text"])
        #     return self.chars[start]["text"]
        pass
