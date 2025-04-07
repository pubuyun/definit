import pdfplumber
import re
from PIL import Image


class Parser:
    IGNORE_PAGE_FOOTER_Y = 35
    PAGE_NUMBER_Y = 790.4778
    LAST_PAGE_COPYRIGHT_Y = 134
    DIFFERENCE = 5
    QUESTION_START_X = 49.6063  # Will be updated
    IMAGE_PATH = "images/"

    def __init__(self, pdf: pdfplumber.PDF, image_prefix: str = ""):
        self.pdf = pdf
        self.chars = self.read_texts()
        self.find_position_constants()
        self.image_prefix = image_prefix

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
        path_prefix: str,
    ):
        image_paths = []
        for i, image in enumerate(page.images):
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
            path = path_prefix + f"_{i+1}.png"
            im.save(path)
            image_paths.append(path)
        return image_paths

    def find_question_starts(self):
        # This method should be overridden in subclasses
        pass

    def parse_question(self, start_index: int, end_index: int, number: int):
        # This method should be overridden in subclasses
        pass
