import re
from dataclasses import dataclass
import pdfplumber
import os
from typing import List, Optional, Tuple
from dataclasses import dataclass


def clean_markdown(text: str) -> str:
    text = re.sub(r"\[Turn over", "", text)

    text = re.sub(r"\*\*\s+\*\*", "", text)
    text = re.sub(r"\*\s+\*", "", text)

    text = re.sub(r"\s*\*\*\s*([^\s*][^*]*[^\s*])\s*\*\*\s*", r"**\1**", text)
    text = re.sub(r"\s*\*\s*([^\s*][^*]*[^\s*])\s*\*\s*", r"*\1*", text)

    return text


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            chars = page.chars
            page_text = ""
            prev_is_bold = False
            prev_is_italic = False
            for char in chars:
                if not char["text"]:
                    continue
                font_name = char.get("fontname", "").lower()
                is_bold = "bold" in font_name
                is_italic = "italic" in font_name
                # format to markdown, concat with previous text
                if is_bold and not prev_is_bold:
                    page_text += "**"
                elif prev_is_bold and not is_bold:
                    page_text += "**"
                if is_italic and not prev_is_italic:
                    page_text += "*"
                elif prev_is_italic and not is_italic:
                    page_text += "*"
                if char["text"] == "*":
                    page_text += r"\*"
                page_text += char["text"]
                prev_is_bold = is_bold
                prev_is_italic = is_italic
            if prev_is_bold:
                page_text += "**"
            if prev_is_italic:
                page_text += "*"

            page_text = clean_markdown(page_text)
            page_text += "\n"

            text += page_text
    return text


def main():
    qp_path = "papers/igcse-biology-0610/0610_w22_qp_42.pdf"
    ms_path = "papers/igcse-biology-0610/0610_w22_ms_42.pdf"

    qp_text = extract_text_from_pdf(qp_path)
    ms_text = extract_text_from_pdf(ms_path)

    with open("output.md", "w", encoding="utf-8") as f:
        f.write("Question Paper:\n")
        f.write(qp_text)
        f.write("\nMark Scheme:\n")
        f.write(ms_text)


if __name__ == "__main__":
    main()
