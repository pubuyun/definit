from pdf2docx import Converter
from pprint import pprint


class Parser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.tables = self.parse()

    def parse(self) -> list[dict[str, str]]:
        cv = Converter(self.pdf_path)
        tables = cv.extract_tables()
        tables = list(filter(self.isms, tables))
        # concatenate tables
        for i in range(len(tables)):
            for j in range(len(tables[i])):
                tables[i][j] = [cell.replace("\n", "").strip() for cell in tables[i][j]]

        if not tables:
            return []

        # Combine tables into one, keeping only one header
        combined_table = tables[0]  # Keep first table with header
        for table in tables[1:]:
            combined_table.extend(table[1:])  # Add rows except header

        # Convert to dictionary format
        headers = combined_table[0]
        rows = []
        for row in combined_table[1:]:
            row_dict = {}
            for i, header in enumerate(headers):
                if i < len(row):  # Only include if row has enough columns
                    row_dict[header] = row[i]
            rows.append(row_dict)

        cv.close()
        return rows

    @staticmethod
    def isms(page_table):
        MSKEYS = [
            "Question",
            "Answer",
            "Marks",
        ]
        stripped = [
            element.strip().replace("\n", "")
            for element in page_table[0]
            if element != ""
        ]
        for key in MSKEYS:
            if key not in stripped:
                return False
        return True


if __name__ == "__main__":
    pdf_path = "papers/igcse-biology-0610/0610_w22_ms_42.pdf"
    parser = Parser(pdf_path)
    pprint(parser.tables)
