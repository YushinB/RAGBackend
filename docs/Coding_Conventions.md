# Coding Conventions for RAG Python Backend

This document outlines the coding standards and conventions for the RAG Python Backend project, based on the pre-commit configuration and best practices. **All code generation and modifications must follow these conventions.**

## Overview

The project uses automated code quality tools configured in `.pre-commit-config.yaml` to enforce consistent coding standards. These tools run automatically before each commit to ensure code quality.

## Code Quality Tools

### 1. **Black Code Formatter**
- **Version**: 25.11.0
- **Python Version**: 3.13
- **Line Length**: 88 characters
- **Purpose**: Automatic code formatting

**Rules:**
```python
# ✅ Correct - Black formatted
def process_document(
    file_path: Path,
    document_id: str,
    extract_images: bool = True
) -> MultiModalContent:
    """Process a document with the specified options."""
    pass

# ❌ Incorrect - Not Black formatted
def process_document(file_path: Path,document_id: str,extract_images: bool=True)->MultiModalContent:
    """Process a document with the specified options."""
    pass
```

### 2. **Ruff Linter and Formatter**
- **Version**: v0.14.4
- **Configuration**: `--fix --exit-non-zero-on-fix`
- **Purpose**: Fast Python linter with auto-fixing

**Key Rules:**
- Import organization
- Unused variable detection
- Code complexity analysis
- Style consistency

```python
# ✅ Correct - Clean imports, no unused variables
from pathlib import Path
from typing import Any

def extract_text(file_path: Path) -> str:
    """Extract text from file."""
    return file_path.read_text()

# ❌ Incorrect - Unused imports, unused variables
import os
from pathlib import Path
from typing import Any, Dict, List

def extract_text(file_path: Path) -> str:
    """Extract text from file."""
    unused_var = "not used"
    content = file_path.read_text()
    return content
```

### 3. **MyPy Type Checker**
- **Version**: v1.18.2
- **Additional Dependencies**: types-requests, types-PyYAML, pydantic
- **Scope**: Excludes tests/ and scripts/

**Type Annotation Requirements:**
```python
# ✅ Correct - Full type annotations
from typing import Optional, Union
from pathlib import Path

class PDFProcessor:
    def __init__(self, **config: Any) -> None:
        self.extract_images: bool = config.get("extract_images", True)

    def extract_text(self, file_path: Union[Path, str]) -> str:
        """Extract text with proper type hints."""
        validated_path = Path(file_path)
        return validated_path.read_text()

    def extract_multimodal_content(
        self,
        file_path: Union[Path, str],
        document_id: str
    ) -> Optional[MultiModalContent]:
        """Extract content with optional return."""
        # Implementation here
        return None

# ❌ Incorrect - Missing or incorrect type annotations
class PDFProcessor:
    def __init__(self, **config):  # Missing return type
        self.extract_images = config.get("extract_images", True)  # Missing type

    def extract_text(self, file_path):  # Missing all type hints
        validated_path = Path(file_path)
        return validated_path.read_text()
```

### 4. **isort Import Sorting**
- **Version**: 7.0.0
- **Profile**: Black compatible
- **Configuration**: `--filter-files`

**Import Organization:**
```python
# ✅ Correct - Organized imports
# Standard library
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

# Third-party
import fitz  # PyMuPDF
from openpyxl import load_workbook
from pydantic import BaseModel

# Local imports
from src.core.debug_logger import PDFDebugLogger
from src.models.base_models import MultiModalContent
from src.processors.base import DataProcessor

# ❌ Incorrect - Random import order
from src.processors.base import DataProcessor
import json
from openpyxl import load_workbook
import os
from src.models.base_models import MultiModalContent
from typing import Any
import fitz
```

### 5. **Bandit Security Scanner**
- **Version**: 1.8.6
- **Configuration**: Recursive scan (`-r`)
- **Scope**: Excludes tests/ and scripts/

**Security Requirements:**
```python
# ✅ Correct - Secure practices
import tempfile
from pathlib import Path

def save_secure_file(content: str) -> Path:
    """Save file securely."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(content)
        return Path(f.name)

def load_config(config_path: Path) -> dict:
    """Load configuration safely."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    return json.loads(config_path.read_text())

# ❌ Incorrect - Security issues
def save_file(content: str, filename: str):
    """Insecure file operations."""
    # Hardcoded paths
    with open(f"/tmp/{filename}", "w") as f:  # Bandit warning
        f.write(content)

def execute_command(cmd: str):
    """Dangerous command execution."""
    import subprocess
    subprocess.call(cmd, shell=True)  # Bandit error - shell injection
```

## Coding Conventions

### 1. **File and Directory Structure**

```
src/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── app.py
│   ├── config.py
│   └── debug_logger.py
├── processors/
│   ├── __init__.py
│   ├── base.py
│   ├── pdf_processor.py
│   └── excel_processor.py
└── models/
    ├── __init__.py
    └── base_models.py
```

### 2. **Naming Conventions**

```python
# ✅ Classes: PascalCase
class PDFProcessor(DataProcessor):
    pass

class MultiModalContent:
    pass

# ✅ Functions and variables: snake_case
def extract_multimodal_content(file_path: Path) -> MultiModalContent:
    document_id = str(uuid4())
    processing_config = {"extract_images": True}
    return process_document(file_path, document_id, processing_config)

# ✅ Constants: UPPER_SNAKE_CASE
MAX_FILE_SIZE = 10 * 1024 * 1024
DEFAULT_CHUNK_SIZE = 512
SUPPORTED_EXTENSIONS = {".pdf", ".xlsx", ".docx"}

# ✅ Private methods: Leading underscore
class DocumentProcessor:
    def _extract_images_from_page(self, page: Any) -> List[ImageContent]:
        """Private helper method."""
        pass

    def _validate_file_format(self, file_path: Path) -> bool:
        """Private validation method."""
        return True
```

### 3. **Documentation Standards**

```python
# ✅ Class documentation
class PDFProcessor(DataProcessor):
    """
    Processor for PDF documents.

    Handles extraction of text, images, tables, and equations from PDF files,
    maintaining relationships between elements and preserving document hierarchy.

    Attributes:
        supported_extensions: Set of file extensions ('.pdf')
        processor_name: Human-readable name ('PDF Processor')

    Example:
        >>> processor = PDFProcessor(extract_images=True)
        >>> content = processor.extract_multimodal_content("document.pdf", "doc_1")
        >>> print(f"Found {len(content.images)} images")
    """

# ✅ Method documentation
def extract_multimodal_content(
    self,
    file_path: Union[Path, str],
    document_id: str
) -> MultiModalContent:
    """
    Extract all content including text, images, tables, and equations.

    This method performs comprehensive extraction of multi-modal content,
    maintaining relationships between elements and preserving document structure.

    Args:
        file_path: Path to the PDF file
        document_id: Unique identifier for this document

    Returns:
        MultiModalContent object with all extracted content and relationships

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the PDF is invalid or corrupted

    Example:
        >>> processor = PDFProcessor()
        >>> content = processor.extract_multimodal_content("doc.pdf", "doc_1")
        >>> print(f"Extracted {len(content.text_chunks)} text chunks")
    """
```

### 4. **Error Handling**

```python
# ✅ Proper exception handling
def extract_text(self, file_path: Union[Path, str]) -> str:
    """Extract text with proper error handling."""
    self.validate_file(file_path)

    try:
        doc = fitz.open(str(file_path))
        text_parts = []

        for page in doc:
            page_text = page.get_text()
            if page_text:
                text_parts.append(page_text)

        doc.close()
        return "\n\n".join(text_parts)

    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {e}") from e

# ✅ Input validation
def validate_file(self, file_path: Union[Path, str]) -> None:
    """Validate file exists and is readable."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    if path.stat().st_size == 0:
        raise ValueError(f"File is empty: {path}")
```

### 5. **Configuration and Dependencies**

```python
# ✅ Proper dependency management
from typing import Any, Optional
from pathlib import Path

class ProcessorConfig:
    """Configuration class with type hints and defaults."""

    def __init__(
        self,
        extract_images: bool = True,
        extract_tables: bool = True,
        max_file_size: int = 10 * 1024 * 1024,
        debug: bool = False,
        debug_level: str = "INFO"
    ) -> None:
        self.extract_images = extract_images
        self.extract_tables = extract_tables
        self.max_file_size = max_file_size
        self.debug = debug
        self.debug_level = debug_level

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "ProcessorConfig":
        """Create configuration from dictionary."""
        return cls(**config_dict)
```

### 6. **Logging Standards**

```python
# ✅ Proper logging with debug system
from src.core.debug_logger import PDFDebugLogger, debug_operation

class PDFProcessor:
    def __init__(self, **config: Any) -> None:
        # Production-aware debug logging
        debug_enabled = config.get("debug", False)
        if debug_enabled:
            self.debug_logger = PDFDebugLogger(auto_detect_production=True)
        else:
            self.debug_logger = PDFDebugLogger(level="ERROR")

    @debug_operation("PDF Text Extraction")
    def extract_text(self, file_path: Union[Path, str]) -> str:
        """Extract text with automatic debug logging."""
        with self.debug_logger.debug_operation("Validate file", file_path=str(file_path)):
            self.validate_file(file_path)

        try:
            with self.debug_logger.debug_operation("Open PDF document"):
                doc = fitz.open(str(file_path))
                self.debug_logger.debug_data("PDF info", f"{len(doc)} pages")

            # Rest of implementation...
            return extracted_text

        except Exception as e:
            self.debug_logger.debug_error("PDF extraction", e)
            raise
```

### 7. **Testing Standards**

```python
# ✅ Test structure (in tests/ directory)
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.processors.pdf_processor import PDFProcessor

class TestPDFProcessor:
    """Test suite for PDF processor."""

    @pytest.fixture
    def processor(self) -> PDFProcessor:
        """Create processor instance for testing."""
        return PDFProcessor(debug=False)

    @pytest.fixture
    def sample_pdf_path(self) -> Path:
        """Provide sample PDF file path."""
        return Path("tests/fixtures/sample.pdf")

    def test_can_process_valid_pdf(self, processor: PDFProcessor, sample_pdf_path: Path) -> None:
        """Test processor can handle valid PDF files."""
        assert processor.can_process(sample_pdf_path) is True

    def test_extract_text_success(self, processor: PDFProcessor, sample_pdf_path: Path) -> None:
        """Test successful text extraction."""
        text = processor.extract_text(sample_pdf_path)
        assert isinstance(text, str)
        assert len(text) > 0

    def test_extract_text_file_not_found(self, processor: PDFProcessor) -> None:
        """Test error handling for missing files."""
        with pytest.raises(FileNotFoundError):
            processor.extract_text("nonexistent.pdf")
```

## Pre-commit Integration

### Running Pre-commit

```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
pre-commit run mypy --all-files

# Update hooks to latest versions
pre-commit autoupdate
```

### Excluded Files and Directories

The following are excluded from pre-commit checks:
- `.git/` - Git internal files
- `.venv/`, `venv/` - Virtual environments
- `.pytest_cache/` - Pytest cache
- `__pycache__/` - Python cache
- `*.pyc` - Compiled Python files
- `data/` - Data files
- `logs/` - Log files
- `.env*` - Environment files

## Agent Code Generation Rules

When generating code, the agent must:

1. **Follow Black formatting** (88 character line length)
2. **Include complete type annotations** for MyPy compatibility
3. **Organize imports** according to isort standards
4. **Write comprehensive docstrings** with Args, Returns, Raises
5. **Handle errors appropriately** with specific exceptions
6. **Use production-aware debug logging** when applicable
7. **Follow security best practices** to pass Bandit checks
8. **Include appropriate test structure** when creating new modules
9. **Use proper naming conventions** (PascalCase for classes, snake_case for functions)
10. **Validate inputs and handle edge cases**

## Configuration Files

### pyproject.toml Integration
The project should include compatible configuration for tools:

```toml
[tool.black]
line-length = 88
target-version = ['py313']

[tool.ruff]
line-length = 88
target-version = "py313"

[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.isort]
profile = "black"
line_length = 88
```

This ensures all code generated follows the established conventions and passes the pre-commit checks automatically.
