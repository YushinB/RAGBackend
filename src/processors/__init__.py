"""Data Processing Module.

This module contains processors for various document formats including:
- PDF documents
- Word documents (.docx)
- Excel spreadsheets (.xlsx)
- Markdown files
- Plain text files

Each processor implements multi-modal content extraction with relationship preservation.
"""

from .base import DataProcessor
from .excel_processor import ExcelProcessor
from .markdown_processor import MarkdownProcessor
from .pdf_processor import PDFProcessor
from .text_processor import TextFileProcessor
from .word_processor import WordProcessor

__all__ = [
    "DataProcessor",
    "ExcelProcessor",
    "MarkdownProcessor",
    "PDFProcessor",
    "TextFileProcessor",
    "WordProcessor",
]
