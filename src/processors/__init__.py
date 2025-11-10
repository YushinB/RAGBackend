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

__all__ = ["DataProcessor"]
