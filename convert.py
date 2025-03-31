from pdf2docx import Converter
from pprint import pprint

pdf_file = "papers/igcse-biology-0610/0610_w22_qp_42.pdf"
docx_file = "output.docx"

# convert pdf to docx
cv = Converter(pdf_file)
# tables = cv.extract_tables(start=6, end=7)
# pprint(tables)
cv.convert(docx_file)  # all pages by default
cv.close()
