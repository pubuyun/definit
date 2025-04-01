import pdfplumber
from typing import List, Tuple


class MarkSchemeParser:
    def __init__(self, pdf: pdfplumber.PDF):
        self.pdf = pdf

    def extract_lines(self) -> List[List[Tuple[float, float]]]:
        lines = []
        for page in self.pdf.pages[5:]:
            page_lines = [(rect["x0"], rect["y0"]) for rect in page.rects]
            lines.append(page_lines)
        return lines
