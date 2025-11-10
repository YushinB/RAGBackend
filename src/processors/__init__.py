"""Data Processing Module.

This module contains processors for various document formats including:
- PDF documents
- Word documents (.docx)
- Excel spreadsheets (.xlsx)
- Markdown files
- Plain text files

Each processor implements multi-modal content extraction with relationship preservation.

Also includes advanced chunking strategies:
- Relationship-aware chunking (T4.2.1)
- Linked chunking (T4.2.2)
- Semantic chunking (T4.2.3)

And processor factory for automatic file type detection (T5.1):
- ProcessorFactory for file type detection and processor selection
- ProcessorRegistry for dynamic processor registration
- Plugin system for custom processors

And error handling/validation (T5.2):
- FileValidator for file validation and security checks
- ErrorHandler for centralized error management
- ProcessingError exceptions for structured error handling
"""

from .base import DataProcessor
from .chunking_strategies import (
    BaseChunker,
    ChunkerFactory,
    LinkedChunker,
    RelationshipAwareChunker,
    SemanticChunker,
)
from .error_handling import (
    ErrorHandler,
    FileValidationError,
    FileValidator,
    ProcessingError,
    ProcessingErrorType,
    SecurityError,
    ValidationConfig,
    create_default_validator,
    validate_file_path,
)
from .excel_processor import ExcelProcessor
from .factory import (
    ProcessorFactory,
    ProcessorFactoryBuilder,
    ProcessorRegistry,
    get_default_factory,
    process_file,
)
from .markdown_processor import MarkdownProcessor
from .pdf_processor import PDFProcessor
from .text_processor import TextFileProcessor
from .word_processor import WordProcessor

__all__ = [
    "BaseChunker",
    "ChunkerFactory",
    "DataProcessor",
    "ErrorHandler",
    "ExcelProcessor",
    "FileValidationError",
    "FileValidator",
    "LinkedChunker",
    "MarkdownProcessor",
    "PDFProcessor",
    "ProcessingError",
    "ProcessingErrorType",
    "ProcessorFactory",
    "ProcessorFactoryBuilder",
    "ProcessorRegistry",
    "RelationshipAwareChunker",
    "SecurityError",
    "SemanticChunker",
    "TextFileProcessor",
    "ValidationConfig",
    "WordProcessor",
    "create_default_validator",
    "get_default_factory",
    "process_file",
    "validate_file_path",
]
