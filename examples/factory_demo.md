# ProcessorFactory Usage Guide

## Overview

The `ProcessorFactory` provides automatic file type detection and processor selection for the RAG system. It eliminates the need to manually choose processors for different file formats.

## Features

- **Automatic Detection**: Detects file types by extension and MIME type
- **19 Supported Extensions**: `.pdf`, `.docx`, `.doc`, `.xlsx`, `.xls`, `.md`, `.markdown`, `.txt`, `.text`, `.log`, `.csv`, `.json`, `.xml`, `.html`, etc.
- **5 Built-in Processors**: PDF, Word, Excel, Markdown, and Text processors
- **Plugin System**: Register custom processors dynamically
- **Builder Pattern**: Flexible factory configuration
- **Singleton Support**: Convenient default factory instance

## Quick Start

### Basic Usage

```python
from src.processors.factory import get_default_factory

# Get the default factory
factory = get_default_factory()

# Check if a file can be processed
if factory.can_process("document.pdf"):
    processor = factory.get_processor_for_file("document.pdf")
    content = processor.process("document.pdf")
```

### Convenience Function

```python
from src.processors.factory import process_file

# Process file directly - one line!
content = process_file("document.pdf")
content = process_file("data.xlsx", extract_formulas=True)
content = process_file("README.md")
```

## Supported File Types

### PDF Documents
- Extensions: `.pdf`
- Processor: `PDFProcessor`
- Features: Text extraction, image extraction, table detection

### Word Documents
- Extensions: `.docx`, `.doc`
- Processor: `WordProcessor`
- Features: Text extraction, formatting preservation, image extraction

### Excel Spreadsheets
- Extensions: `.xlsx`, `.xls`
- Processor: `ExcelProcessor`
- Features: Multi-sheet support, formula extraction, data validation

### Markdown Files
- Extensions: `.md`, `.markdown`
- Processor: `MarkdownProcessor`
- Features: Structured parsing, code block detection, link extraction

### Text Files
- Extensions: `.txt`, `.text`, `.log`, `.csv`, `.json`, `.xml`, `.html`
- Processor: `TextFileProcessor`
- Features: Encoding detection, plain text extraction

## Advanced Features

### Custom Processor Registration

```python
from src.processors.factory import ProcessorFactory
from src.processors.base import DataProcessor
from src.models.base_models import MultiModalContent

class CustomProcessor(DataProcessor):
    def can_process(self, file_path: str) -> bool:
        return file_path.endswith(".custom")

    def extract_text(self, file_path: str) -> str:
        # Implementation
        return "extracted text"

    def extract_multimodal_content(self, file_path: str) -> MultiModalContent:
        # Implementation
        return MultiModalContent(document_id="custom")

    def chunk_text(self, text: str, config: dict | None = None) -> list:
        # Implementation
        return [text]

    def process(self, file_path: str, **kwargs) -> MultiModalContent:
        # Implementation
        return MultiModalContent(document_id="custom")

# Register the custom processor
factory = ProcessorFactory()
factory.register_custom_processor(
    name="custom",
    processor_class=CustomProcessor,
    extensions=[".custom", ".cst"],
    mime_types=["application/x-custom"]
)

# Use it
processor = factory.get_processor_for_file("data.custom")
```

### Builder Pattern Configuration

```python
from src.processors.factory import ProcessorFactoryBuilder

factory = (
    ProcessorFactoryBuilder()
    .with_processor("latex", LatexProcessor, [".tex", ".latex"])
    .with_processor("bibtex", BibtexProcessor, [".bib"])
    .build()
)

# Factory now supports LaTeX and BibTeX files
processor = factory.get_processor_for_file("paper.tex")
```

### Batch Processing

```python
from src.processors.factory import get_default_factory

factory = get_default_factory()

files = [
    "chapter1.pdf",
    "notes.docx",
    "data.xlsx",
    "README.md",
    "config.json"
]

results = []
for file_path in files:
    if factory.can_process(file_path):
        processor = factory.get_processor_for_file(file_path)
        content = processor.process(file_path)
        results.append(content)
```

### Configuration Passing

```python
factory = get_default_factory()

# Pass configuration to processor
processor = factory.get_processor_for_file(
    "document.pdf",
    extract_images=True,
    ocr_enabled=False
)

# Or use process_file convenience function
content = factory.process_file(
    "data.xlsx",
    extract_formulas=True,
    sheet_name="Summary"
)
```

## File Type Detection

The factory uses a two-stage detection process:

1. **Extension Matching** (Primary)
   - Case-insensitive
   - Matches against registered extensions
   - Fast and reliable for most files

2. **MIME Type Fallback** (Secondary)
   - Used when extension doesn't match
   - Detects actual file content type
   - Handles edge cases and misnamed files

```python
factory = ProcessorFactory()

# Detect file type
extension, mime_type = factory.detect_file_type("document.pdf")
# Returns: ('.pdf', 'application/pdf')

# Get processor for file
processor = factory.get_processor_for_file("document.pdf")
# Returns: PDFProcessor instance
```

## Error Handling

```python
from src.processors.factory import ProcessorFactory

factory = ProcessorFactory()

try:
    # Check if file can be processed
    if not factory.can_process("unknown.xyz"):
        print("File type not supported")

    # Process file
    content = factory.process_file("document.pdf")

except FileNotFoundError:
    print("File not found")
except ValueError as e:
    print(f"Processing error: {e}")
```

## Registry Isolation

Each factory instance has its own independent registry:

```python
from src.processors.factory import ProcessorFactory

# Factory 1 with custom processor
factory1 = ProcessorFactory()
factory1.register_custom_processor("custom1", CustomProcessor1, [".c1"])

# Factory 2 with different custom processor
factory2 = ProcessorFactory()
factory2.register_custom_processor("custom2", CustomProcessor2, [".c2"])

# Registries are isolated
assert factory1.can_process("file.c1")  # True
assert factory1.can_process("file.c2")  # False
assert factory2.can_process("file.c1")  # False
assert factory2.can_process("file.c2")  # True
```

## Best Practices

1. **Use Convenience Functions**
   ```python
   # Simple case - just process the file
   content = process_file("document.pdf")
   ```

2. **Check Support Before Processing**
   ```python
   if factory.can_process(file_path):
       content = factory.process_file(file_path)
   ```

3. **Pass Configuration as Needed**
   ```python
   processor = factory.get_processor_for_file(
       file_path,
       extract_images=True,
       custom_option="value"
   )
   ```

4. **Use Builder for Complex Setups**
   ```python
   factory = (
       ProcessorFactoryBuilder()
       .with_processor("type1", Processor1, [".ext1"])
       .with_processor("type2", Processor2, [".ext2"])
       .build()
   )
   ```

5. **Leverage Default Factory for Simple Cases**
   ```python
   factory = get_default_factory()  # Singleton
   ```

## Implementation Details

### Architecture

```
ProcessorFactory
├── ProcessorRegistry (plugin system)
│   ├── Register processors by name
│   ├── Map extensions to processors
│   └── Map MIME types to processors
├── File type detection
│   ├── Extension matching (primary)
│   └── MIME type detection (fallback)
└── Processor instantiation
    ├── Configuration passing
    └── Error handling
```

### Performance

- **Fast Extension Matching**: O(1) lookup in dict
- **Lazy Instantiation**: Processors created only when needed
- **Registry Caching**: Default processors registered once
- **Singleton Pattern**: Default factory reused across calls

## See Also

- [Processor API Reference](../src/processors/README.md)
- [Data Models](../src/models/README.md)
- [Chunking Strategies](chunking_example.py)
