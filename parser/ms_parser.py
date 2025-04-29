from pdf2docx import Converter
import fitz  # PyMuPDF
import os
from pprint import pprint


class Parser:
    IMAGE_PATH = "images/"

    def __init__(self, pdf_path: str, image_prefix: str = "example"):
        self.pdf_path = pdf_path
        self.image_prefix = image_prefix
        self.tables = self.parse()

    def parse(self) -> list[dict[str, str]]:
        # Initialize converter
        cv = Converter(self.pdf_path)
        fitz_pdf = fitz.open(self.pdf_path)

        # Get default settings and make sure ocr setting exists
        settings = cv.default_settings

        try:
            # Parse PDF pages with proper settings
            cv.parse(**settings)

            combined = []

            # Process each parsed page
            for page in cv.pages:
                if not page.finalized:
                    continue

                # Get table blocks from page by navigating through sections and columns
                table_blocks = []
                for section in page.sections:
                    for column in section:
                        if settings["extract_stream_table"]:
                            table_blocks.extend(column.blocks.table_blocks)
                        else:
                            table_blocks.extend(column.blocks.lattice_table_blocks)

                for table_block in table_blocks:
                    headers = []
                    table_content = []
                    for header in table_block[0]:
                        if header:
                            text = header.text.replace("\n", "").strip()
                            headers.append(text)
                        else:
                            headers.append("")
                    # Check if the table is a valid MS table
                    if not self.isms(headers):
                        continue
                    # Process each row except header in the table
                    for i, row in enumerate(table_block[1:]):
                        row_content = []
                        for cell in row:
                            if cell:
                                text = cell.text.replace("\n", "").strip()
                                row_content.append(text)
                            else:
                                row_content.append("")

                        row_content_dict = {
                            header: row_content[j] for j, header in enumerate(headers)
                        }

                        row_bbox = row.bbox  # Get the bounding box of the table block
                        matrix = fitz.Matrix(2, 2)  # Increase resolution
                        fitz_page = fitz_pdf[page.id]

                        pix = fitz_page.get_pixmap(matrix=matrix, clip=row_bbox)
                        # Save the image of the row
                        image_path = (
                            self.IMAGE_PATH
                            + self.image_prefix
                            + "_"
                            + row_content_dict["Question"].replace(" ", "_")
                            + ".png"
                        )
                        pix.save(image_path)
                        print(f"Saved row image to {image_path}")

                        row_content_dict["Image"] = image_path
                        # Add row content and position to respective lists
                        table_content.append(row_content_dict)
                    combined.extend(table_content)
        finally:
            # Close the converter
            cv.close()
            fitz_pdf.close()

        return combined

    @staticmethod
    def isms(page_table):
        MSKEYS = [
            "Question",
            "Answer",
        ]
        stripped = [
            element.strip().replace("\n", "") for element in page_table if element != ""
        ]
        for key in MSKEYS:
            if key not in stripped:
                return False
        return True


if __name__ == "__main__":
    pdf_path = "papers/igcse-biology-0610/0610_w22_ms_42.pdf"
    parser = Parser(pdf_path, image_prefix="0610_w22_ms_42")

    # Print example of the first row
    if parser.tables:
        for i, row in enumerate(parser.tables):
            print(row["Question"])
            print(row["Answer"])
            print("Image", row["Image"])
            print("-" * 80)
