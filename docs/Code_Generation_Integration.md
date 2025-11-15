# Code Generation Integration Guide

This guide explains how to apply the established coding standards to all code generation for this RAG Python Backend project.

## Quick Start

When generating code for this project, follow these steps:

### 1. Import Standards Module
```python
from src.utils.agent_standards import (
    validate_and_fix_code,
    generate_code_with_standards,
    CODE_TEMPLATES,
    ensure_code_quality
)
```

### 2. Use Templates for Common Patterns

#### Creating a New Processor Class
```python
# Use the processor_class template
code = generate_code_with_standards(
    CODE_TEMPLATES["processor_class"],
    processor_name="JSONProcessor",
    file_type="JSON",
    processor_description="Processes JSON documents and extracts structured data.",
    extensions="{'.json', '.jsonl'}",
    display_name="JSON Document Processor",
    config_description="- max_depth: Maximum nesting depth to process",
    config_initialization="self.max_depth = config.get('max_depth', 10)",
    text_extraction_implementation="return json.dumps(json.load(Path(file_path).open()))",
    multimodal_extraction_implementation="# Implementation here"
)
```

#### Creating a New Function
```python
code = generate_code_with_standards(
    CODE_TEMPLATES["function_definition"],
    function_name="process_chunk",
    parameters="chunk_data: dict[str, Any], chunk_id: str",
    return_type="TextChunk",
    function_description="Process a data chunk into a TextChunk object.",
    args_description="chunk_data: Raw chunk data\\n        chunk_id: Unique identifier for the chunk",
    returns_description="Processed TextChunk object",
    raises_description="ValueError: If chunk_data is invalid",
    example="process_chunk({'text': 'Hello'}, 'chunk_1')",
    implementation="return TextChunk(id=chunk_id, text=chunk_data['text'])"
)
```

### 3. Validate Generated Code

For any code string, always validate before presenting:

```python
# Method 1: Validate and auto-fix
fixed_code, was_initially_valid = validate_and_fix_code(generated_code)

# Method 2: Use decorator for code-generating functions
@ensure_code_quality
def generate_my_code():
    return "def example(): pass"  # Your generated code here
```

## Coding Standards Checklist

Before presenting any generated code, ensure it meets these requirements:

### ✅ Formatting (Black v25.11.0)
- [ ] Line length: 88 characters maximum
- [ ] 4-space indentation
- [ ] Double quotes for strings
- [ ] Proper spacing around operators

### ✅ Type Hints (MyPy v1.18.2)
- [ ] All public functions have type hints
- [ ] Use modern Python 3.13+ syntax: `list[str]` not `List[str]`
- [ ] Return type annotations for all functions
- [ ] Parameter type annotations

### ✅ Imports (isort v7.0.0)
- [ ] Standard library imports first
- [ ] Third-party imports second
- [ ] Local imports last
- [ ] Remove unused imports
- [ ] Black-compatible sorting

### ✅ Docstrings (Google Style)
- [ ] All public classes have docstrings
- [ ] All public functions have docstrings
- [ ] Include Args, Returns, Raises sections
- [ ] Include usage examples where helpful

### ✅ Security (Bandit v1.8.6)
- [ ] No hardcoded passwords or secrets
- [ ] Safe file operations using pathlib
- [ ] Proper input validation
- [ ] No use of unsafe functions like `eval()`

### ✅ Code Quality (Ruff v0.14.4)
- [ ] No unused variables
- [ ] Proper exception handling
- [ ] No overly complex functions
- [ ] Follow naming conventions

## Standard Import Patterns

### For Processor Classes
```python
from pathlib import Path
from typing import Any, Union
from uuid import uuid4

from src.core.debug_logger import (
    PDFDebugLogger,
    debug_operation,
    get_production_safe_debug_logger
)
from src.models.base_models import MultiModalContent, TextChunk
from src.processors.base import DataProcessor
```

### For Utility Functions
```python
from pathlib import Path
from typing import Any, Optional

from src.core.exceptions import ProcessingError
from src.core.logging import get_logger
```

### For API Endpoints
```python
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel, Field

from src.core.exceptions import ValidationError
from src.core.logging import get_logger
```

## Example: Complete Processor Generation

Here's how to generate a complete, standards-compliant processor:

```python
from src.utils.agent_standards import generate_code_with_standards, CODE_TEMPLATES

# Generate processor class
processor_code = generate_code_with_standards(
    CODE_TEMPLATES["processor_class"],
    processor_name="CSVProcessor",
    file_type="CSV",
    processor_description="""Processes CSV files and converts them to structured text.

    Handles various CSV dialects and encodings, extracting both tabular
    data and generating readable text representations.""",
    extensions="{'.csv', '.tsv'}",
    display_name="CSV File Processor",
    config_description="""- encoding: File encoding (default: 'utf-8')
                - delimiter: Column delimiter (default: ',')
                - has_header: Whether first row is header (default: True)""",
    config_initialization="""self.encoding = config.get('encoding', 'utf-8')
        self.delimiter = config.get('delimiter', ',')
        self.has_header = config.get('has_header', True)""",
    text_extraction_implementation="""import csv

            with Path(file_path).open(encoding=self.encoding) as f:
                reader = csv.reader(f, delimiter=self.delimiter)
                rows = list(reader)

                if not rows:
                    return ""

                if self.has_header:
                    headers = rows[0]
                    data_rows = rows[1:]

                    result = f"CSV Data with columns: {', '.join(headers)}\\n\\n"
                    for i, row in enumerate(data_rows, 1):
                        result += f"Row {i}:\\n"
                        for header, value in zip(headers, row):
                            result += f"  {header}: {value}\\n"
                        result += "\\n"
                    return result
                else:
                    return "\\n".join([",".join(row) for row in rows])""",
    multimodal_extraction_implementation="""# Extract text content
            text_content = self.extract_text(file_path)

            # Create content object
            content = MultiModalContent(
                document_id=document_id,
                text_content=text_content,
                images=[],
                tables=[],
                equations=[],
                metadata={
                    "processor": self.processor_name,
                    "file_path": str(file_path),
                    "encoding": self.encoding,
                    "delimiter": self.delimiter,
                    "has_header": self.has_header
                }
            )

            return content"""
)

# The generated code is automatically formatted and validated
print(processor_code)
```

## Integration with Debug Logging

All generated processors should include production-aware debug logging:

```python
# In __init__ method
debug_enabled = config.get("debug", False)
debug_level = config.get("debug_level", "DEBUG")
if debug_enabled:
    self.debug_logger = PDFDebugLogger(level=debug_level, auto_detect_production=True)
else:
    self.debug_logger = get_production_safe_debug_logger()

# In processing methods
@debug_operation("Operation Name")
def process_data(self, data):
    with self.debug_logger.debug_operation("Detailed step", data_info="..."):
        # Processing logic here
        pass
```

## Pre-commit Integration

The project uses these pre-commit hooks that automatically run on commit:

1. **trailing-whitespace**: Removes trailing spaces
2. **end-of-file-fixer**: Ensures files end with newline
3. **check-yaml/json/toml**: Validates config file syntax
4. **debug-statements**: Removes debug print statements
5. **black**: Formats code (88 char line length)
6. **ruff**: Lints and auto-fixes code issues
7. **mypy**: Type checks with strict configuration
8. **isort**: Sorts imports (Black profile)
9. **bandit**: Scans for security vulnerabilities

All generated code is automatically compatible with these hooks.

## Quick Validation

To quickly check if generated code meets standards:

```python
from src.utils.code_style_validator import validate_generated_code

code = "def example(): pass"
is_valid, report = validate_generated_code(code)
if not is_valid:
    print(report)
```

This ensures all code generated for the project maintains consistent quality and follows established conventions automatically.
