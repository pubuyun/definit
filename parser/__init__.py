from PIL import Image
import pdfplumber
import re
from typing import List
from .qp_parser import Parser
from .mcq_parser import MCQParser
from .sq_parser import QuestionPaperParser
from .markscheme import MarkSchemeParser


__all__ = [
    "Parser",
    "MCQParser",
    "QuestionPaperParser",
    "MarkSchemeParser",
]
